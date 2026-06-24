package dev.harrypulvirenti.fire2mqtt.ui

import android.app.Application
import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.data.PermissionChecker
import dev.harrypulvirenti.fire2mqtt.data.ProvisioningConfig
import dev.harrypulvirenti.fire2mqtt.data.SettingsRepository
import dev.harrypulvirenti.fire2mqtt.mqtt.ConnectionTester
import dev.harrypulvirenti.fire2mqtt.mqtt.TestResult
import dev.harrypulvirenti.fire2mqtt.service.Fire2MqttService
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.koin.android.annotation.KoinViewModel

@KoinViewModel
class SetupViewModel(
    private val app: Application,
    private val repository: SettingsRepository,
    private val permissionChecker: PermissionChecker,
    private val connectionTester: ConnectionTester,
    /** Dispatchers.IO in production (AppModule); injectable so tests stay deterministic. */
    private val ioDispatcher: CoroutineDispatcher,
) : ViewModel() {

    private val _state: MutableStateFlow<SetupUiState>

    /** Collected by the Compose UI. */
    val state: StateFlow<SetupUiState>

    /**
     * The initial DataStore load below. [applyProvisioning] joins it before writing so a slow
     * first load can't resolve last and clobber the pushed broker config back to the defaults.
     */
    private val initialLoad: Job

    init {
        // Seed an empty (ready = false) state, then populate off the main thread. The
        // launch splash (MainActivity) stays up until ready = true, so the settings read +
        // Settings.Secure writes + network enumeration below never block the first frame.
        _state = MutableStateFlow(SetupUiState())
        state = _state.asStateFlow()
        initialLoad = viewModelScope.launch {
            val s = repository.load() // DataStore reads on its own IO executor
            val snap = permSnapshot()
            _state.value = _state.value.copy(
                host        = s.host,
                port        = s.port,
                username    = s.username,
                password    = s.password,
                useTls      = s.useTls,
                deviceId    = s.deviceId,
                topicPrefix = s.topicPrefix,
                connection  = ConnState.Disconnected,
                connectionMessage = if (s.host.isBlank()) TextValue.TextResource(R.string.msg_no_broker)
                                    else TextValue.TextResource(R.string.msg_not_tested),
                ready       = true,
            ).withPerms(snap)
                // Re-assert live service state in case the collector below ran first
                // (the copy above resets connection to Disconnected).
                .applyServiceRunning(Fire2MqttService.running.value)
        }
        // Mirror the service's actual lifecycle instead of setting flags optimistically:
        // this also catches the service stopping itself (blank host, fatal MQTT error).
        viewModelScope.launch {
            Fire2MqttService.running.collect { running ->
                _state.value = _state.value.applyServiceRunning(running)
            }
        }
    }

    private fun SetupUiState.applyServiceRunning(running: Boolean): SetupUiState = when {
        running -> copy(
            isServiceRunning  = true,
            connection        = ConnState.Running,
            connectionMessage = TextValue.TextResource(R.string.msg_publishing),
        )
        // Falling edge: the service was running and is now gone. The broker was
        // reachable while it ran, so fall back to Connected (matches pre-flow behavior).
        isServiceRunning -> copy(
            isServiceRunning  = false,
            connection        = ConnState.Connected,
            connectionMessage = TextValue.TextResource(R.string.msg_service_stopped),
        )
        else -> this
    }

    // -------------------------------------------------------------------------
    // Field setters (hoisted to the UI as lambdas). UI state updates synchronously
    // so typing stays responsive; persistence is a suspend DataStore write
    // (serialized in launch order on the main-dispatcher viewModelScope).
    // -------------------------------------------------------------------------

    fun updateHost(value: String) {
        viewModelScope.launch { repository.setHost(value) }
        _state.value = _state.value.copy(
            host = value,
            connection = ConnState.Disconnected,
            connectionMessage = if (value.isBlank()) TextValue.TextResource(R.string.msg_no_broker)
                                else TextValue.TextResource(R.string.msg_not_tested),
        )
    }

    fun updatePort(value: Int) {
        viewModelScope.launch { repository.setPort(value) }
        _state.value = _state.value.copy(port = value)
    }

    fun updateUsername(value: String) {
        viewModelScope.launch { repository.setUsername(value) }
        _state.value = _state.value.copy(username = value)
    }

    fun updatePassword(value: String) {
        viewModelScope.launch { repository.setPassword(value) }
        _state.value = _state.value.copy(password = value)
    }

    fun updateDeviceId(value: String) {
        viewModelScope.launch { repository.setDeviceId(value) }
        _state.value = _state.value.copy(deviceId = value)
    }

    fun updateTopicPrefix(value: String) {
        viewModelScope.launch { repository.setTopicPrefix(value) }
        _state.value = _state.value.copy(topicPrefix = value)
    }

    fun updateUseTls(value: Boolean) {
        viewModelScope.launch { repository.setUseTls(value) }
        _state.value = _state.value.copy(
            useTls = value,
            // Toggling transport invalidates any prior probe result.
            connection = ConnState.Disconnected,
            connectionMessage = if (_state.value.host.isBlank())
                TextValue.TextResource(R.string.msg_no_broker)
            else TextValue.TextResource(R.string.msg_not_tested),
        )
    }

    /**
     * Apply broker settings pushed by HA's ADB provisioning (parsed in [MainActivity]).
     * Persists the provided fields, then reflects them in the UI so the dashboard opens
     * pre-filled with no remote typing. See [dev.harrypulvirenti.fire2mqtt.data.ProvisioningConfig].
     */
    fun applyProvisioning(config: ProvisioningConfig) {
        viewModelScope.launch {
            // Wait out the init load first: both write _state with no inherent ordering, and on a
            // fresh install the init load yields blanks — letting it land last would erase the
            // pushed config. Joining makes provisioning deterministically win.
            initialLoad.join()
            repository.applyProvisioning(config)
            val s = repository.load()
            _state.value = _state.value.copy(
                host        = s.host,
                port        = s.port,
                username    = s.username,
                password    = s.password,
                useTls      = s.useTls,
                deviceId    = s.deviceId,
                topicPrefix = s.topicPrefix,
                connection  = ConnState.Disconnected,
                connectionMessage = if (s.host.isBlank())
                    TextValue.TextResource(R.string.msg_no_broker)
                else TextValue.TextResource(R.string.msg_not_tested),
            )
        }
    }

    // -------------------------------------------------------------------------
    // Connection / service control
    // -------------------------------------------------------------------------

    fun testConnection() {
        val current = _state.value
        if (current.host.isBlank()) {
            _state.value = current.copy(
                connection        = ConnState.Failed,
                connectionMessage = TextValue.TextResource(R.string.msg_no_host),
            )
            return
        }

        _state.value = current.copy(
            connection        = ConnState.Testing,
            connectionMessage = TextValue.TextResource(R.string.msg_connecting, listOf(current.host, current.port)),
        )

        viewModelScope.launch {
            val settings = repository.load()
            val result = connectionTester.test(settings)
            _state.value = _state.value.copy(
                connection        = when (result) {
                    is TestResult.Connected -> ConnState.Connected
                    else                   -> ConnState.Failed
                },
                connectionMessage = when (result) {
                    is TestResult.Connected ->
                        TextValue.TextResource(R.string.msg_connected, listOf(result.host, result.port))
                    is TestResult.TimedOut  ->
                        TextValue.TextResource(R.string.msg_timed_out, listOf(result.host, result.port))
                    is TestResult.BadHost   ->
                        TextValue.TextResource(R.string.msg_bad_host, listOf(result.host))
                    is TestResult.NoHost    ->
                        TextValue.TextResource(R.string.msg_no_host)
                    is TestResult.Failed    ->
                        TextValue.TextResource(R.string.msg_failed, listOf(result.reason))
                },
            )
        }
    }

    fun startService() {
        if (!_state.value.canStart) return
        // ContextCompat handles the API < 26 path (plain startService) — minSdk is 25.
        // UI state follows via the Fire2MqttService.running collector in init.
        androidx.core.content.ContextCompat.startForegroundService(
            app, Intent(app, Fire2MqttService::class.java),
        )
    }

    fun stopService() {
        // UI state follows via the Fire2MqttService.running collector in init.
        app.stopService(Intent(app, Fire2MqttService::class.java))
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

    /** Live permission snapshot. Reads (and self-enables) on the IO dispatcher. */
    private data class PermSnapshot(
        val perms: Perms,
        val wss: Boolean,
        val adbIp: String,
    )

    private suspend fun permSnapshot(): PermSnapshot = withContext(ioDispatcher) {
        val wss = permissionChecker.hasWriteSecureSettings()
        // Once WRITE_SECURE_SETTINGS is held, self-enable both accesses automatically.
        if (wss) permissionChecker.enableAll()
        PermSnapshot(
            perms = Perms(
                accessibility = permissionChecker.hasAccessibility(),
                notification  = permissionChecker.hasNotification(),
            ),
            wss   = wss,
            adbIp = localIp(),
        )
    }

    private fun SetupUiState.withPerms(snap: PermSnapshot): SetupUiState = copy(
        perms               = snap.perms,
        writeSecureSettings = snap.wss,
        adbIp               = snap.adbIp,
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
