package dev.harrypulvirenti.fire2mqtt.system

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.provider.Settings
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.commands.Fire2MqttAccessibilityService
import dev.harrypulvirenti.fire2mqtt.media.MediaNotificationListener

private val logger = Logger.withTag("Fire2MQTT/SecureSettings")

/**
 * Enables the app's own accessibility service and notification-listener access by writing the
 * relevant Settings.Secure entries directly.
 *
 * On Fire OS, sideloaded apps cannot be toggled in the Accessibility / Notification-access UI
 * (the settings intents do not resolve, and the app is not listed). The only reliable path on
 * modern Fire OS is to grant WRITE_SECURE_SETTINGS once via ADB
 * (`adb shell pm grant <pkg> android.permission.WRITE_SECURE_SETTINGS`), after which the app
 * writes these secure settings itself — no per-permission ADB, and it works on Fire OS versions
 * that block `adb shell settings put secure ...` directly.
 *
 * PACKAGE_USAGE_STATS is intentionally not handled here: it is an appop, not a secure setting,
 * so WRITE_SECURE_SETTINGS cannot grant it. Foreground detection runs on the accessibility
 * service instead (see [ForegroundAppWatcher]).
 */
object SecureSettingsManager {

    private const val SECURE_ACCESSIBILITY_SERVICES = "enabled_accessibility_services"
    private const val SECURE_ACCESSIBILITY_ENABLED = "accessibility_enabled"
    private const val SECURE_NOTIFICATION_LISTENERS = "enabled_notification_listeners"

    private fun accessibilityComponent(context: Context): String =
        ComponentName(context, Fire2MqttAccessibilityService::class.java).flattenToString()

    private fun notificationListenerComponent(context: Context): String =
        ComponentName(context, MediaNotificationListener::class.java).flattenToString()

    fun hasWriteSecureSettings(context: Context): Boolean =
        context.checkSelfPermission(Manifest.permission.WRITE_SECURE_SETTINGS) ==
            PackageManager.PERMISSION_GRANTED

    fun isAccessibilityEnabled(context: Context): Boolean =
        readComponentList(context, SECURE_ACCESSIBILITY_SERVICES)
            .contains(accessibilityComponent(context)) &&
            Settings.Secure.getInt(context.contentResolver, SECURE_ACCESSIBILITY_ENABLED, 0) == 1

    fun isNotificationListenerEnabled(context: Context): Boolean =
        readComponentList(context, SECURE_NOTIFICATION_LISTENERS)
            .contains(notificationListenerComponent(context))

    /**
     * Idempotently enables accessibility + notification-listener access when WRITE_SECURE_SETTINGS
     * is held. No-op (with a warning) otherwise. Returns true if, after running, both are enabled.
     */
    fun ensureAllEnabled(context: Context): Boolean {
        if (!hasWriteSecureSettings(context)) {
            logger.w {
                "WRITE_SECURE_SETTINGS not granted — cannot self-enable permissions. " +
                    "Run: adb shell pm grant ${context.packageName} " +
                    "android.permission.WRITE_SECURE_SETTINGS"
            }
            return false
        }
        runCatching {
            addComponent(context, SECURE_ACCESSIBILITY_SERVICES, accessibilityComponent(context))
            Settings.Secure.putInt(context.contentResolver, SECURE_ACCESSIBILITY_ENABLED, 1)
            addComponent(context, SECURE_NOTIFICATION_LISTENERS, notificationListenerComponent(context))
            logger.i { "Self-enabled accessibility + notification-listener access" }
        }.onFailure {
            logger.e(it) { "Failed to write secure settings: ${it.message}" }
            return false
        }
        return isAccessibilityEnabled(context) && isNotificationListenerEnabled(context)
    }

    private fun readComponentList(context: Context, key: String): Set<String> =
        Settings.Secure.getString(context.contentResolver, key)
            ?.split(':')
            ?.filter { it.isNotBlank() }
            ?.toSet()
            ?: emptySet()

    private fun addComponent(context: Context, key: String, component: String) {
        val current = readComponentList(context, key)
        if (component in current) return
        val updated = (current + component).joinToString(":")
        Settings.Secure.putString(context.contentResolver, key, updated)
    }
}
