package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.content.Intent
import co.touchlab.kermit.Logger
import org.koin.core.annotation.Factory

private val logger = Logger.withTag("Fire2MQTT/AppLauncher")

/**
 * Launches *other* installed apps on this device by package name — e.g. Home Assistant
 * publishing `com.disney.disneyplus` to `{prefix}/{deviceId}/cmd/launch` to open Disney+
 * on the Fire TV. This is the executor for the `cmd/launch` command (routed by
 * [CommandRouter]); it does not relaunch Fire2MQTT itself.
 */
@Factory
class AppLauncher(private val context: Context) {

    /**
     * Opens the app whose package is [packageName] via its launcher intent.
     * @return true if the app was launched, false if no such launchable package is installed.
     */
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
