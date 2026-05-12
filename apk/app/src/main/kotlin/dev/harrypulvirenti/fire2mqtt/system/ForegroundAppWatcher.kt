package dev.harrypulvirenti.fire2mqtt.system

import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.util.Log
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

private const val TAG = "Fire2MQTT/ForegroundApp"
private const val POLL_INTERVAL_MS = 1_000L

data class ForegroundAppEvent(val packageName: String, val appName: String)

class ForegroundAppWatcher(private val context: Context) {

    private val usageStats = context.getSystemService(UsageStatsManager::class.java)
    private val pm = context.packageManager

    fun foregroundAppFlow(): Flow<ForegroundAppEvent> = flow {
        var lastPackage = ""
        while (true) {
            delay(POLL_INTERVAL_MS)
            val current = getCurrentForegroundPackage()
            if (current != null && current != lastPackage) {
                lastPackage = current
                val name = runCatching { pm.getApplicationLabel(pm.getApplicationInfo(current, 0)).toString() }
                    .getOrDefault(current)
                emit(ForegroundAppEvent(current, name))
            }
        }
    }

    private fun getCurrentForegroundPackage(): String? {
        return try {
            val now = System.currentTimeMillis()
            val events = usageStats.queryEvents(now - 5_000L, now)
            val event = UsageEvents.Event()
            var lastForeground: String? = null
            while (events.hasNextEvent()) {
                events.getNextEvent(event)
                if (event.eventType == UsageEvents.Event.MOVE_TO_FOREGROUND) {
                    lastForeground = event.packageName
                }
            }
            lastForeground
        } catch (e: Exception) {
            Log.e(TAG, "Failed to query usage events: ${e.message}")
            null
        }
    }
}
