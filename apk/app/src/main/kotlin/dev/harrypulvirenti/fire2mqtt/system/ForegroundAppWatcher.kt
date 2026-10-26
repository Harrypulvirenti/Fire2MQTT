package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.commands.Fire2MqttAccessibilityService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map

private val logger = Logger.withTag("Fire2MQTT/ForegroundApp")

// How long after another app takes the foreground a launcher window event is treated as a
// stale echo rather than a real return to the home screen.
internal const val LAUNCHER_FLICKER_WINDOW_MS = 1_000L

// Home-screen packages whose window events can trail behind the app the user just opened.
internal val LAUNCHER_PACKAGES = setOf(
    "com.amazon.tv.launcher",
    "com.amazon.firetv.launcher",
    "com.google.android.apps.tv.launcherx",  // Google TV
    "com.google.android.tvlauncher",  // Android TV (pre-Google TV)
)

data class ForegroundAppEvent(val packageName: String, val appName: String)

/**
 * Reports the foreground app. Detection is driven by [Fire2MqttAccessibilityService],
 * which emits the package of each window that comes to the foreground
 * (TYPE_WINDOW_STATE_CHANGED). This replaces UsageStatsManager polling — the
 * PACKAGE_USAGE_STATS permission cannot be granted to a sideloaded app on Fire OS,
 * whereas the accessibility service is already required for key injection and can be
 * enabled via WRITE_SECURE_SETTINGS.
 *
 * On Google TV the launcher fires a window event *after* the app it just opened (same second),
 * which would report "Google TV" while YouTube is on screen; such launcher echoes are dropped.
 */
class ForegroundAppWatcher(
    private val context: Context,
    private val source: Flow<String> = Fire2MqttAccessibilityService.foregroundPackages,
    private val nowMs: () -> Long = { System.nanoTime() / 1_000_000 },
) {

    private val pm = context.packageManager

    fun foregroundAppFlow(): Flow<ForegroundAppEvent> =
        source
            .dropLauncherFlicker()
            .distinctUntilChanged()
            .map { pkg ->
                val name = runCatching {
                    pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString()
                }.getOrElse {
                    logger.d { "No label for $pkg — falling back to package name" }
                    pkg
                }
                ForegroundAppEvent(pkg, name)
            }

    private fun Flow<String>.dropLauncherFlicker(): Flow<String> = flow {
        var lastEmitted: String? = null
        var lastAppAtMs: Long? = null
        collect { pkg ->
            val now = nowMs()
            if (pkg in LAUNCHER_PACKAGES) {
                val sinceApp = lastAppAtMs?.let { now - it }
                if (sinceApp != null && sinceApp < LAUNCHER_FLICKER_WINDOW_MS) {
                    logger.d { "Ignoring launcher event $pkg ${sinceApp}ms after an app took focus" }
                    return@collect
                }
            } else if (pkg != lastEmitted) {
                // Only an app *taking* focus opens the window; repeat events from inside the
                // same app mustn't swallow a real HOME press that follows them.
                lastAppAtMs = now
            }
            lastEmitted = pkg
            emit(pkg)
        }
    }
}
