package dev.harrypulvirenti.fire2mqtt.ui

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.PreferenceManager
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.service.Fire2MqttService

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
        }

        // Guide user through required permissions
        if (!hasUsageStatsPermission()) {
            startActivity(Intent(this, PermissionsActivity::class.java))
        }
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = getSystemService(android.app.AppOpsManager::class.java)
        val mode = appOps.checkOpNoThrow(
            android.app.AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            packageName,
        )
        return mode == android.app.AppOpsManager.MODE_ALLOWED
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
