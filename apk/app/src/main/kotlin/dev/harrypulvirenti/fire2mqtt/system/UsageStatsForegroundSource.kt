package dev.harrypulvirenti.fire2mqtt.system

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.os.PowerManager
import android.os.Process
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.commands.Fire2MqttAccessibilityService
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

private val logger = Logger.withTag("Fire2MQTT/UsageStats")

// Fallback cadence. A local binder query per second is cheap, and MQTT still only publishes
// when the foreground package actually changes (ForegroundAppWatcher dedupes).
private const val POLL_MS = 1_000L
// Re-check cadence while there's nothing to do (accessibility bound, screen off, no access).
private const val IDLE_POLL_MS = 5_000L
// How far back the first query looks, so an app opened before we started is still reported.
private const val INITIAL_LOOKBACK_MS = 60 * 60 * 1000L

/**
 * Foreground-app fallback for devices that refuse the accessibility service. Fire OS 6.7
 * (1st-gen Fire TV Stick 4K and similar) runs every third-party accessibility service past
 * an Amazon allowlist (`A11yAuthorizer … trust=false` in `logcat -b all`) and never binds
 * ours, whatever enabled_accessibility_services says.
 *
 * Reads MOVE_TO_FOREGROUND events from UsageStatsManager. That needs the GET_USAGE_STATS
 * appop, which the app can't grant itself but ADB can
 * (`appops set <pkg> GET_USAGE_STATS allow`; the integration's provisioning runs it).
 * UsageStats has no change callback, so this polls, but only while the accessibility service
 * is unbound and the screen is on. It's the one exception to the APK's push-only rule.
 */
class UsageStatsForegroundSource(
    private val context: Context,
    private val accessibilityBound: () -> Boolean = { Fire2MqttAccessibilityService.instance != null },
) {

    fun hasUsageAccess(): Boolean = hasUsageAccess(context)

    fun packages(): Flow<String> = flow {
        val usage = context.getSystemService(UsageStatsManager::class.java)
        val power = context.getSystemService(PowerManager::class.java)
        var since: Long? = null
        var active = false
        while (true) {
            val usable = !accessibilityBound() && power.isInteractive && hasUsageAccess()
            if (usable != active) {
                active = usable
                logger.i { if (usable) "Polling usage stats for the foreground app" else "Usage-stats polling paused" }
            }
            if (!usable) {
                delay(IDLE_POLL_MS)
                continue
            }
            val now = System.currentTimeMillis()
            val events = readForegroundEvents(usage, since ?: (now - INITIAL_LOOKBACK_MS), now)
            latestForeground(events, context.packageName)?.let { emit(it) }
            // Next window starts just after the newest event we saw (or now if none).
            since = (events.maxOfOrNull { it.second } ?: (now - 1)) + 1
            delay(POLL_MS)
        }
    }

    private fun readForegroundEvents(usage: UsageStatsManager, from: Long, to: Long): List<Pair<String, Long>> {
        val result = mutableListOf<Pair<String, Long>>()
        val events = usage.queryEvents(from, to) ?: return result
        val event = UsageEvents.Event()
        while (events.getNextEvent(event)) {
            if (event.eventType == UsageEvents.Event.MOVE_TO_FOREGROUND) {
                result += event.packageName to event.timeStamp
            }
        }
        return result
    }

    companion object {
        /**
         * The package of the newest foreground event in [events] (package to timestamp pairs),
         * skipping our own UI as the accessibility path does. Null when there's nothing new.
         */
        internal fun latestForeground(events: List<Pair<String, Long>>, ownPackage: String): String? =
            events.filter { it.first != ownPackage && it.first.isNotBlank() }
                .maxByOrNull { it.second }
                ?.first

        fun hasUsageAccess(context: Context): Boolean {
            val appOps = context.getSystemService(AppOpsManager::class.java) ?: return false
            @Suppress("DEPRECATION") // unsafeCheckOpNoThrow is API 29+; minSdk is 25.
            val mode = appOps.checkOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                context.packageName,
            )
            return mode == AppOpsManager.MODE_ALLOWED
        }
    }
}
