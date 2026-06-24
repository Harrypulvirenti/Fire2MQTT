package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import android.content.Intent
import org.koin.core.annotation.Factory

/**
 * Enumerates the launchable apps installed on this device so Home Assistant can offer
 * only the apps that are actually present (published on `state/apps`).
 *
 * Both the phone-style `CATEGORY_LAUNCHER` and the TV `CATEGORY_LEANBACK_LAUNCHER` are
 * queried and unioned — Fire TV apps frequently register only the leanback entry, the
 * same reason a plain `getLaunchIntentForPackage` can miss them. `QUERY_ALL_PACKAGES`
 * (declared in the manifest) makes the enumeration visible on Android 11+.
 */
@Factory
class InstalledAppsProvider(private val context: Context) {

    /** Distinct package names of every launchable app, excluding Fire2MQTT itself. */
    fun launchablePackages(): List<String> {
        val pm = context.packageManager
        val packages = linkedSetOf<String>()
        for (category in CATEGORIES) {
            val intent = Intent(Intent.ACTION_MAIN)
            intent.addCategory(category)
            @Suppress("DEPRECATION") // the ResolveInfoFlags overload is API 33+; minSdk is 25
            pm.queryIntentActivities(intent, 0).forEach { resolved ->
                resolved.activityInfo?.packageName?.let(packages::add)
            }
        }
        packages.remove(context.packageName)
        return packages.toList()
    }

    private companion object {
        val CATEGORIES = listOf(Intent.CATEGORY_LAUNCHER, Intent.CATEGORY_LEANBACK_LAUNCHER)
    }
}
