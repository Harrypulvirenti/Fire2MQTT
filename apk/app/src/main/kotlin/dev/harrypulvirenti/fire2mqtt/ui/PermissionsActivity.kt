package dev.harrypulvirenti.fire2mqtt.ui

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.system.SecureSettingsManager
import java.net.NetworkInterface

/**
 * Handles the two special permissions Fire2MQTT needs:
 *   1. Accessibility service — key injection + foreground-app detection.
 *   2. Notification-listener access — MediaSessionManager.getActiveSessions().
 *
 * Both are enabled programmatically once WRITE_SECURE_SETTINGS is granted. On Fire OS the
 * standard settings intents do not resolve for sideloaded apps, so this screen never relies on
 * them: if WRITE_SECURE_SETTINGS is present it self-enables; otherwise it shows the single
 * one-time ADB bootstrap command the user must run.
 */
class PermissionsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_permissions)

        findViewById<Button>(R.id.btn_enable).setOnClickListener {
            if (SecureSettingsManager.ensureAllEnabled(this)) {
                Toast.makeText(this, R.string.perm_enabled_ok, Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, R.string.perm_enabled_fail, Toast.LENGTH_LONG).show()
            }
            render()
        }

        findViewById<Button>(R.id.btn_refresh).setOnClickListener { render() }
        findViewById<Button>(R.id.btn_done).setOnClickListener { finish() }
    }

    override fun onResume() {
        super.onResume()
        // Re-check after the user may have run the ADB command and tabbed back.
        SecureSettingsManager.ensureAllEnabled(this)
        render()
    }

    private fun render() {
        val hasWss = SecureSettingsManager.hasWriteSecureSettings(this)
        val accessibility = SecureSettingsManager.isAccessibilityEnabled(this)
        val notifications = SecureSettingsManager.isNotificationListenerEnabled(this)

        findViewById<TextView>(R.id.tv_status).text = buildString {
            appendLine("${tick(accessibility)} Accessibility (keys + app detection)")
            append("${tick(notifications)} Notification access (media state)")
        }

        val enableBtn = findViewById<Button>(R.id.btn_enable)
        val commandView = findViewById<TextView>(R.id.tv_command)
        val instructionsView = findViewById<TextView>(R.id.tv_instructions)

        if (hasWss) {
            // We can self-enable — hide the ADB instructions, offer the one-tap button.
            instructionsView.text = getString(R.string.perm_have_wss)
            commandView.visibility = TextView.GONE
            enableBtn.visibility = Button.VISIBLE
            enableBtn.isEnabled = !(accessibility && notifications)
        } else {
            // Need the one-time bootstrap grant. Show the exact command + this device's IP.
            instructionsView.text = getString(R.string.perm_need_wss)
            commandView.visibility = TextView.VISIBLE
            commandView.text = getString(R.string.perm_adb_command, localIp())
            enableBtn.visibility = Button.GONE
        }
    }

    private fun tick(granted: Boolean): String = if (granted) "✅" else "❌"

    private fun localIp(): String = try {
        NetworkInterface.getNetworkInterfaces().toList()
            .flatMap { it.inetAddresses.toList() }
            .firstOrNull { !it.isLoopbackAddress && it.hostAddress?.contains(':') == false }
            ?.hostAddress ?: "<fire-tv-ip>"
    } catch (_: Exception) {
        "<fire-tv-ip>"
    }
}
