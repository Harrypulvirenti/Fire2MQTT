package dev.harrypulvirenti.fire2mqtt.data

import android.content.Context
import dev.harrypulvirenti.fire2mqtt.system.SecureSettingsManager

/**
 * Thin seam over [SecureSettingsManager] for the UI/ViewModel. The app needs exactly two
 * special accesses — Accessibility + Notification-listener — both self-enabled via
 * WRITE_SECURE_SETTINGS. (Usage Access was dropped: foreground detection runs on the
 * accessibility service, and PACKAGE_USAGE_STATS can't be self-granted on Fire OS.)
 */
class PermissionChecker(private val context: Context) {

    /** Whether the one-time WRITE_SECURE_SETTINGS ADB grant is held. */
    fun hasWriteSecureSettings(): Boolean =
        SecureSettingsManager.hasWriteSecureSettings(context)

    fun hasAccessibility(): Boolean =
        SecureSettingsManager.isAccessibilityEnabled(context)

    fun hasNotification(): Boolean =
        SecureSettingsManager.isNotificationListenerEnabled(context)

    /** Idempotently self-enable both accesses; returns true if both are on afterwards. */
    fun enableAll(): Boolean =
        SecureSettingsManager.ensureAllEnabled(context)
}
