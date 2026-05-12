package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.content.Intent
import android.util.Log

private const val TAG = "Fire2MQTT/AppLauncher"

class AppLauncher(private val context: Context) {

    fun launch(packageName: String): Boolean {
        val intent = context.packageManager.getLaunchIntentForPackage(packageName)
            ?: run {
                Log.w(TAG, "No launch intent found for $packageName")
                return false
            }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        Log.i(TAG, "Launched $packageName")
        return true
    }
}
