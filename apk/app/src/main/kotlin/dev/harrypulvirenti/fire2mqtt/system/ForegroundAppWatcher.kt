package dev.harrypulvirenti.fire2mqtt.system

import android.content.Context
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.commands.Fire2MqttAccessibilityService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map

private val logger = Logger.withTag("Fire2MQTT/ForegroundApp")

data class ForegroundAppEvent(val packageName: String, val appName: String)

/**
 * Reports the foreground app. Detection is driven by [Fire2MqttAccessibilityService],
 * which emits the package of each window that comes to the foreground
 * (TYPE_WINDOW_STATE_CHANGED). This replaces UsageStatsManager polling — the
 * PACKAGE_USAGE_STATS permission cannot be granted to a sideloaded app on Fire OS,
 * whereas the accessibility service is already required for key injection and can be
 * enabled via WRITE_SECURE_SETTINGS.
 */
class ForegroundAppWatcher(
    private val context: Context,
    private val source: Flow<String> = Fire2MqttAccessibilityService.foregroundPackages,
) {

    private val pm = context.packageManager

    fun foregroundAppFlow(): Flow<ForegroundAppEvent> =
        source
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
}
