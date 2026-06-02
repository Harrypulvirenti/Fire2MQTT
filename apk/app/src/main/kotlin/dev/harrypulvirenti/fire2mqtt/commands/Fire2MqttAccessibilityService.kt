package dev.harrypulvirenti.fire2mqtt.commands

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.media.AudioManager
import android.view.KeyEvent
import android.view.accessibility.AccessibilityEvent
import co.touchlab.kermit.Logger

private val logger = Logger.withTag("Fire2MQTT/Accessibility")

/**
 * AccessibilityService used for key event injection (HOME, BACK, DPAD, etc.).
 *
 * Note: INJECT_EVENTS requires system signature for a sideloaded APK. This service
 * provides the only viable alternative — AccessibilityService global actions + key events.
 * User must enable it in Settings > Accessibility.
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

    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit
    override fun onInterrupt() = Unit

    fun dispatchKey(keyCode: Int) {
        val globalAction = when (keyCode) {
            KeyEvent.KEYCODE_HOME -> GLOBAL_ACTION_HOME
            KeyEvent.KEYCODE_BACK -> GLOBAL_ACTION_BACK
            KeyEvent.KEYCODE_APP_SWITCH -> GLOBAL_ACTION_RECENTS
            else -> null
        }
        if (globalAction != null) {
            performGlobalAction(globalAction)
            return
        }
        val am = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, keyCode))
        am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_UP, keyCode))
    }

    companion object {
        var instance: Fire2MqttAccessibilityService? = null

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
