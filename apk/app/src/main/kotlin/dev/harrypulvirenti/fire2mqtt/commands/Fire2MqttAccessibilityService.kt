package dev.harrypulvirenti.fire2mqtt.commands

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.media.AudioManager
import android.os.Build
import android.view.KeyEvent
import android.view.accessibility.AccessibilityEvent
import co.touchlab.kermit.Logger
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

private val logger = Logger.withTag("Fire2MQTT/Accessibility")

/**
 * AccessibilityService used for two things:
 *   1. Key event injection (HOME, BACK, DPAD, etc.) via [sendKey].
 *   2. Foreground-app detection via TYPE_WINDOW_STATE_CHANGED — published on
 *      [foregroundPackages]. This replaces UsageStatsManager (PACKAGE_USAGE_STATS),
 *      which cannot be granted on Fire OS for a sideloaded app.
 *
 * Note: INJECT_EVENTS requires system signature for a sideloaded APK. This service
 * provides the only viable alternative — AccessibilityService global actions + key events.
 * The service is enabled programmatically via WRITE_SECURE_SETTINGS (see SecureSettingsManager).
 *
 * Key presses are dispatched by calling the static [sendKey] method from the service,
 * which is called by [CommandRouter].
 */
class Fire2MqttAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        logger.i { "Accessibility service connected" }
        instance = this
    }

    override fun onUnbind(intent: android.content.Intent?): Boolean {
        instance = null
        return super.onUnbind(intent)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event?.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return
        val pkg = event.packageName?.toString() ?: return
        // Ignore our own UI and obvious non-app windows (system UI / IME overlays).
        if (pkg == packageName || pkg.isBlank()) return
        foregroundPackagesMutable.tryEmit(pkg)
    }

    override fun onInterrupt() = Unit

    fun dispatchKey(keyCode: Int) {
        // A sideloaded app can't inject raw key events (needs system INJECT_EVENTS), so
        // navigation/system keys go through AccessibilityService global actions. DPAD actions
        // are API 30+ (Fire OS 11) — without them arrow navigation can't be delivered at all.
        globalActionFor(keyCode, Build.VERSION.SDK_INT)?.let {
            performGlobalAction(it)
            return
        }
        // Media transport keys still route through the active media session.
        val am = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, keyCode))
        am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_UP, keyCode))
    }

    companion object {
        var instance: Fire2MqttAccessibilityService? = null

        /**
         * Maps a key code to the AccessibilityService global action that delivers it, or null
         * when none applies (those keys fall back to the media-session path). DPAD navigation
         * actions only exist on API 30+ (Android 11 / Fire OS 11). Pure for testing.
         */
        internal fun globalActionFor(keyCode: Int, sdkInt: Int): Int? = when (keyCode) {
            KeyEvent.KEYCODE_HOME -> GLOBAL_ACTION_HOME
            KeyEvent.KEYCODE_BACK -> GLOBAL_ACTION_BACK
            KeyEvent.KEYCODE_APP_SWITCH -> GLOBAL_ACTION_RECENTS
            KeyEvent.KEYCODE_DPAD_UP -> dpadAction(GLOBAL_ACTION_DPAD_UP, sdkInt)
            KeyEvent.KEYCODE_DPAD_DOWN -> dpadAction(GLOBAL_ACTION_DPAD_DOWN, sdkInt)
            KeyEvent.KEYCODE_DPAD_LEFT -> dpadAction(GLOBAL_ACTION_DPAD_LEFT, sdkInt)
            KeyEvent.KEYCODE_DPAD_RIGHT -> dpadAction(GLOBAL_ACTION_DPAD_RIGHT, sdkInt)
            KeyEvent.KEYCODE_DPAD_CENTER -> dpadAction(GLOBAL_ACTION_DPAD_CENTER, sdkInt)
            else -> null
        }

        private fun dpadAction(action: Int, sdkInt: Int): Int? =
            if (sdkInt >= Build.VERSION_CODES.R) action else null

        // Buffered (replay=1) so a late collector still sees the current foreground app.
        private val foregroundPackagesMutable = MutableSharedFlow<String>(
            replay = 1,
            extraBufferCapacity = 8,
        )

        /** Emits the package name of each app that comes to the foreground. */
        val foregroundPackages: SharedFlow<String> = foregroundPackagesMutable.asSharedFlow()

        fun sendKey(keyCode: Int): Boolean {
            return instance?.let {
                it.dispatchKey(keyCode)
                true
            } ?: run {
                logger.w { "AccessibilityService not connected — key $keyCode dropped" }
                false
            }
        }
    }
}
