package dev.harrypulvirenti.fire2mqtt.ui

import android.app.Application
import android.content.Intent
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.data.PermissionChecker
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository
import dev.harrypulvirenti.fire2mqtt.mqtt.ConnectionTester
import dev.harrypulvirenti.fire2mqtt.mqtt.TestResult
import dev.harrypulvirenti.fire2mqtt.service.Fire2MqttService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class SetupViewModel(app: Application) : AndroidViewModel(app) {

    private val repository = SettingsRepository(app)
    private val permissionChecker = PermissionChecker(app)

    private fun str(resId: Int, vararg args: Any): String =
        getApplication<Application>().getString(resId, *args)

    private val _state: MutableStateFlow<SetupUiState>

    /** Collected by the Compose UI. */
    val state: StateFlow<SetupUiState>

    init {
        // Seed an empty (ready = false) state, then populate off the main thread. The
        // launch splash (MainActivity) stays up until ready = true, so the disk read +
        // Settings.Secure writes + network enumeration below never block the first frame.
        _state = MutableStateFlow(SetupUiState())
        state = _state.asStateFlow()
        viewModelScope.launch {
            val s = withContext(Dispatchers.IO) { repository.load() }
            val snap = permSnapshot()
            _state.value = _state.value.copy(
                host        = s.host,
                port        = s.port,
                username    = s.username,
                password    = s.password,
                deviceId    = s.deviceId,
                topicPrefix = s.topicPrefix,
                connection  = ConnState.Disconnected,
                connectionMessage = if (s.host.isBlank()) str(R.string.msg_no_broker)
                                    else str(R.string.msg_not_tested),
                ready       = true,
            ).withPerms(snap)
        }
    }

    // -------------------------------------------------------------------------
    // Field setters (hoisted to the UI as lambdas)
    // -------------------------------------------------------------------------

    fun updateHost(value: String) {
        repository.setHost(value)
        _state.value = _state.value.copy(
            host = value,
            connection = ConnState.Disconnected,
            connectionMessage = if (value.isBlank()) str(R.string.msg_no_broker)
                                else str(R.string.msg_not_tested),
        )
    }

    fun updatePort(value: Int) {
        repository.setPort(value)
        _state.value = _state.value.copy(port = value)
    }

    fun updateUsername(value: String) {
        repository.setUsername(value)
        _state.value = _state.value.copy(username = value)
    }

    fun updatePassword(value: String) {
        repository.setPassword(value)
        _state.value = _state.value.copy(password = value)
    }

    fun updateDeviceId(value: String) {
        repository.setDeviceId(value)
        _state.value = _state.value.copy(deviceId = value)
    }

    fun updateTopicPrefix(value: String) {
        repository.setTopicPrefix(value)
        _state.value = _state.value.copy(topicPrefix = value)
    }

    // -------------------------------------------------------------------------
    // Connection / service control
    // -------------------------------------------------------------------------

    fun testConnection() {
        val current = _state.value
        if (current.host.isBlank()) {
            _state.value = current.copy(
                connection        = ConnState.Failed,
                connectionMessage = str(R.string.msg_no_host),
            )
            return
        }

        _state.value = current.copy(
            connection        = ConnState.Testing,
            connectionMessage = str(R.string.msg_connecting, current.host, current.port),
        )

        viewModelScope.launch {
            val settings = repository.load()
            val result = ConnectionTester().test(settings)
            _state.value = _state.value.copy(
                connection        = when (result) {
                    is TestResult.Connected -> ConnState.Connected
                    else                   -> ConnState.Failed
                },
                connectionMessage = when (result) {
                    is TestResult.Connected ->
                        str(R.string.msg_connected, result.host, result.port)
                    is TestResult.TimedOut  ->
                        str(R.string.msg_timed_out, result.host, result.port)
                    is TestResult.BadHost   ->
                        str(R.string.msg_bad_host, result.host)
                    is TestResult.NoHost    ->
                        str(R.string.msg_no_host)
                    is TestResult.Failed    ->
                        str(R.string.msg_failed, result.reason)
                },
            )
        }
    }

    fun startService() {
        if (!_state.value.canStart) return
        val app = getApplication<Application>()
        // ContextCompat handles the API < 26 path (plain startService) — minSdk is 25.
        androidx.core.content.ContextCompat.startForegroundService(
            app, Intent(app, Fire2MqttService::class.java),
        )
        _state.value = _state.value.copy(
            isServiceRunning  = true,
            connection        = ConnState.Running,
            connectionMessage = str(R.string.msg_publishing),
        )
    }

    fun stopService() {
        val app = getApplication<Application>()
        app.stopService(Intent(app, Fire2MqttService::class.java))
        val wasRunning = _state.value.connection == ConnState.Running
        _state.value = _state.value.copy(
            isServiceRunning  = false,
            connection        = if (wasRunning) ConnState.Connected else ConnState.Disconnected,
            connectionMessage = str(R.string.msg_service_stopped),
        )
    }

    /**
     * Re-read live permission state (call from MainActivity.onResume and the "Re-check"
     * button). Auto-runs self-enable when WRITE_SECURE_SETTINGS is held. Off the main thread.
     */
    fun refreshPermissions() {
        viewModelScope.launch {
            val snap = permSnapshot()
            _state.value = _state.value.withPerms(snap)
        }
    }

    /** Live permission/service snapshot. Reads (and self-enables) on the IO dispatcher. */
    private data class PermSnapshot(
        val perms: Perms,
        val wss: Boolean,
        val adbIp: String,
        val serviceRunning: Boolean,
    )

    private suspend fun permSnapshot(): PermSnapshot = withContext(Dispatchers.IO) {
        val wss = permissionChecker.hasWriteSecureSettings()
        // Once WRITE_SECURE_SETTINGS is held, self-enable both accesses automatically.
        if (wss) permissionChecker.enableAll()
        PermSnapshot(
            perms = Perms(
                accessibility = permissionChecker.hasAccessibility(),
                notification  = permissionChecker.hasNotification(),
            ),
            wss            = wss,
            adbIp          = localIp(),
            serviceRunning = Fire2MqttService.isRunning,
        )
    }

    private fun SetupUiState.withPerms(snap: PermSnapshot): SetupUiState = copy(
        perms               = snap.perms,
        writeSecureSettings = snap.wss,
        adbIp               = snap.adbIp,
        isServiceRunning    = snap.serviceRunning,
        connection          = if (snap.serviceRunning) ConnState.Running
                              else connection.takeUnless { it == ConnState.Running }
                                  ?: ConnState.Disconnected,
    )

    /** This device's LAN IPv4 (mirrors Fire2MqttService.getLocalIpAddress) for the ADB command. */
    private fun localIp(): String = try {
        java.net.NetworkInterface.getNetworkInterfaces().toList()
            .flatMap { it.inetAddresses.toList() }
            .firstOrNull { !it.isLoopbackAddress && it.hostAddress?.contains(':') == false }
            ?.hostAddress ?: "<device-ip>"
    } catch (_: Exception) {
        "<device-ip>"
    }
}
