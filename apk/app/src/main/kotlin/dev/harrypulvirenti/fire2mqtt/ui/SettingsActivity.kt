package dev.harrypulvirenti.fire2mqtt.ui

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceManager
import com.hivemq.client.mqtt.mqtt5.Mqtt5Client
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.mqtt.BrokerHostValidator
import dev.harrypulvirenti.fire2mqtt.service.Fire2MqttService
import dev.harrypulvirenti.fire2mqtt.system.SecureSettingsManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.settings_container, SettingsFragment())
                .commit()
        }

        findViewById<Button>(R.id.btn_start_service)?.setOnClickListener {
            val intent = Intent(this, Fire2MqttService::class.java)
            startForegroundService(intent)
            Toast.makeText(this, "Fire2MQTT service started", Toast.LENGTH_SHORT).show()
            finishAffinity()
        }

        val testBtn = findViewById<Button>(R.id.btn_test_connection)
        testBtn?.setOnClickListener {
            testBtn.isEnabled = false
            testBtn.text = getString(R.string.btn_test_connection_testing)
            lifecycleScope.launch {
                val result = probeConnection()
                testBtn.isEnabled = true
                testBtn.text = getString(R.string.btn_test_connection)
                Toast.makeText(this@SettingsActivity, result, Toast.LENGTH_LONG).show()
            }
        }

        // Self-enable accessibility + notification-listener access if WRITE_SECURE_SETTINGS is
        // held. If anything is still missing, send the user to the permissions screen.
        SecureSettingsManager.ensureAllEnabled(this)
        if (!SecureSettingsManager.isAccessibilityEnabled(this) ||
            !SecureSettingsManager.isNotificationListenerEnabled(this)
        ) {
            startActivity(Intent(this, PermissionsActivity::class.java))
        }
    }

    private suspend fun probeConnection(): String = withContext(Dispatchers.IO) {
        val prefs = getPrefs(this@SettingsActivity)
        val host = prefs.getString("broker_host", "") ?: ""
        val port = prefs.getString("broker_port", "1883")?.toIntOrNull() ?: 1883
        val username = prefs.getString("broker_username", null)?.takeIf { it.isNotBlank() }
        val password = prefs.getString("broker_password", null)?.takeIf { it.isNotBlank() }

        if (host.isBlank()) return@withContext "No broker host configured"

        val resolvedHost = BrokerHostValidator.resolveToPrivateAddress(host)
            ?: return@withContext "Cannot resolve '$host' — use an RFC1918 IP or LAN hostname"

        val builder = Mqtt5Client.builder()
            .identifier("fire2mqtt_probe_${UUID.randomUUID()}")
            .serverHost(resolvedHost)
            .serverPort(port)

        if (username != null) {
            val auth = builder.simpleAuth().username(username)
            password?.let { auth.password(it.toByteArray()) }
            auth.applySimpleAuth()
        }

        val client = builder.buildAsync()
        return@withContext try {
            client.connectWith()
                .cleanStart(true)
                .send()
                .get(5, TimeUnit.SECONDS)
            client.disconnectWith().send()
            "Connected to $host:$port"
        } catch (e: TimeoutException) {
            runCatching { client.disconnectWith().send() }
            "Timed out connecting to $host:$port"
        } catch (e: Exception) {
            runCatching { client.disconnectWith().send() }
            val cause = e.cause?.message ?: e.message ?: "unknown error"
            "Failed: $cause"
        }
    }

    class SettingsFragment : PreferenceFragmentCompat() {
        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            setPreferencesFromResource(R.xml.preferences, rootKey)
        }
    }

    companion object {
        fun getPrefs(context: Context): SharedPreferences =
            PreferenceManager.getDefaultSharedPreferences(context)
    }
}
