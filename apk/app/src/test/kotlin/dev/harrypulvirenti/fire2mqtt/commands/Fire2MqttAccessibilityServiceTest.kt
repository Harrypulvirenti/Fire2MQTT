package dev.harrypulvirenti.fire2mqtt.commands

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.view.KeyEvent
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityWindowInfo
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class Fire2MqttAccessibilityServiceTest {

    private fun action(keyCode: Int, sdk: Int = Build.VERSION_CODES.R) =
        Fire2MqttAccessibilityService.globalActionFor(keyCode, sdk)

    @Test fun `home, back and recents map to global actions on any api`() {
        assertEquals(AccessibilityService.GLOBAL_ACTION_HOME, action(KeyEvent.KEYCODE_HOME, sdk = 25))
        assertEquals(AccessibilityService.GLOBAL_ACTION_BACK, action(KeyEvent.KEYCODE_BACK, sdk = 25))
        assertEquals(AccessibilityService.GLOBAL_ACTION_RECENTS, action(KeyEvent.KEYCODE_APP_SWITCH, sdk = 25))
    }

    @Test fun `dpad keys map to dpad global actions on api 30+`() {
        assertEquals(AccessibilityService.GLOBAL_ACTION_DPAD_UP, action(KeyEvent.KEYCODE_DPAD_UP))
        assertEquals(AccessibilityService.GLOBAL_ACTION_DPAD_DOWN, action(KeyEvent.KEYCODE_DPAD_DOWN))
        assertEquals(AccessibilityService.GLOBAL_ACTION_DPAD_LEFT, action(KeyEvent.KEYCODE_DPAD_LEFT))
        assertEquals(AccessibilityService.GLOBAL_ACTION_DPAD_RIGHT, action(KeyEvent.KEYCODE_DPAD_RIGHT))
        assertEquals(AccessibilityService.GLOBAL_ACTION_DPAD_CENTER, action(KeyEvent.KEYCODE_DPAD_CENTER))
    }

    @Test fun `dpad keys are unavailable before api 30`() {
        assertNull(action(KeyEvent.KEYCODE_DPAD_DOWN, sdk = 29))
    }

    @Test fun `media and unknown keys have no global action`() {
        // These fall back to the media-session path.
        assertNull(action(KeyEvent.KEYCODE_MEDIA_PLAY))
        assertNull(action(KeyEvent.KEYCODE_MENU))
    }

    private fun windowOf(id: Int, type: Int): AccessibilityWindowInfo =
        mockk<AccessibilityWindowInfo>().also {
            every { it.id } returns id
            every { it.type } returns type
        }

    @Test fun `application window is trusted`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))

        assertTrue(Fire2MqttAccessibilityService.isApplicationWindow(1, windows))
    }

    @Test fun `system chrome window is rejected`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_SYSTEM))

        assertFalse(Fire2MqttAccessibilityService.isApplicationWindow(1, windows))
    }

    @Test fun `input method window is rejected`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_INPUT_METHOD))

        assertFalse(Fire2MqttAccessibilityService.isApplicationWindow(1, windows))
    }

    @Test fun `unknown window id is allowed through rather than blocking detection`() {
        val windows = listOf(windowOf(2, AccessibilityWindowInfo.TYPE_APPLICATION))

        assertTrue(Fire2MqttAccessibilityService.isApplicationWindow(1, windows))
    }

    @Test fun `null window list is allowed through`() {
        assertTrue(Fire2MqttAccessibilityService.isApplicationWindow(1, null))
    }

    private fun eventOf(
        type: Int = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED,
        packageName: CharSequence? = "com.other.app",
        windowId: Int = 1,
    ): AccessibilityEvent =
        mockk<AccessibilityEvent>().also {
            every { it.eventType } returns type
            every { it.packageName } returns packageName
            every { it.windowId } returns windowId
        }

    // These exercise the exact function onAccessibilityEvent calls in production, not a
    // reimplementation of its logic — so a regression in the wiring itself would be caught here.

    @Test fun `window-state change for another app on an application window is reported`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))
        val event = eventOf(packageName = "com.other.app", windowId = 1)

        assertEquals(
            "com.other.app",
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }

    @Test fun `system-type window during playback is not reported as an app switch`() {
        // Reproduces the reported bug: Apple TV starts playback and a system overlay
        // (quick settings / captions panel) fires TYPE_WINDOW_STATE_CHANGED on top of it.
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_SYSTEM))
        val event = eventOf(packageName = "com.amazon.tv.systemui", windowId = 1)

        assertNull(
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }

    @Test fun `own package is never reported`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))
        val event = eventOf(packageName = "com.fire2mqtt", windowId = 1)

        assertNull(
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }

    @Test fun `blank package is never reported`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))
        val event = eventOf(packageName = "", windowId = 1)

        assertNull(
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }

    @Test fun `null package is never reported`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))
        val event = eventOf(packageName = null, windowId = 1)

        assertNull(
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }

    @Test fun `non window-state-changed events are ignored`() {
        val windows = listOf(windowOf(1, AccessibilityWindowInfo.TYPE_APPLICATION))
        val event = eventOf(type = AccessibilityEvent.TYPE_VIEW_CLICKED, windowId = 1)

        assertNull(
            Fire2MqttAccessibilityService.decideForegroundPackage(event, "com.fire2mqtt", windows),
        )
    }
}
