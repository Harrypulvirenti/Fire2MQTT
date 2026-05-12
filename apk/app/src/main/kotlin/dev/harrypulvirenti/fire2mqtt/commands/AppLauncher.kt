package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.content.Intent
import co.touchlab.kermit.Logger

private val logger = Logger.withTag("Fire2MQTT/AppLauncher")

class AppLauncher(private val context: Context) {

    fun launch(packageName: String): Boolean {
        val intent = context.packageManager.getLaunchIntentForPackage(packageName)
            ?: run {
                logger.w { "No launch intent found for $packageName" }
                return false
            }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        logger.i { "Launched $packageName" }
        return true
    }
}
