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
        val pm = context.packageManager
        // Fall back to the leanback (TV) launcher: many Fire TV apps register only a
        // CATEGORY_LEANBACK_LAUNCHER activity, for which getLaunchIntentForPackage
        // returns null — the cause of "the button does nothing" for e.g. Crunchyroll.
        val intent = pm.getLaunchIntentForPackage(packageName)
            ?: pm.getLeanbackLaunchIntentForPackage(packageName)
            ?: run {
                logger.w { "No launch intent found for $packageName" }
                return false
            }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        logger.i { "Launched $packageName" }
        return true
    }

    /**
     * Brings up the home screen with a CATEGORY_HOME intent — the HOME fallback when the
     * accessibility service isn't bound (Fire OS 6.7 refuses third-party accessibility services).
     */
    fun goHome() {
        val intent = Intent(Intent.ACTION_MAIN)
            .addCategory(Intent.CATEGORY_HOME)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        runCatching { context.startActivity(intent) }
            .onSuccess { logger.i { "Went home via launcher intent" } }
            .onFailure { logger.e(it) { "Could not open the home screen: ${it.message}" } }
    }
}
