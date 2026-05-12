package dev.harrypulvirenti.fire2mqtt.ui

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import dev.harrypulvirenti.fire2mqtt.R

/**
 * Walks the user through granting the two non-automatic permissions:
 *   1. PACKAGE_USAGE_STATS — required for foreground app detection
 *   2. Notification listener access — required for MediaSessionManager
 *
 * Both must be granted manually in system settings. This activity shows
 * instructions and deep-links the user to the correct settings screens.
 */
class PermissionsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_permissions)

        val instructions = listOf(
            "1. Tap 'Grant Usage Access' below → find Fire2MQTT → enable it.",
            "2. Tap 'Grant Notification Access' below → find Fire2MQTT → enable it.",
            "3. Tap 'Grant Accessibility Access' below → find Fire2MQTT → enable it.",
            "4. Return here and tap 'I'm Done'.",
        ).joinToString("\n\n")

        findViewById<TextView>(R.id.tv_instructions).text = instructions

        findViewById<Button>(R.id.btn_usage_access).setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }

        findViewById<Button>(R.id.btn_notification_access).setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }

        findViewById<Button>(R.id.btn_accessibility_access).setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        findViewById<Button>(R.id.btn_done).setOnClickListener {
            finish()
        }
    }
}
