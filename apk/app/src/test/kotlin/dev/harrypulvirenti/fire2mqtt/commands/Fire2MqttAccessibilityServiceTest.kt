package dev.harrypulvirenti.fire2mqtt.commands

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.view.KeyEvent
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
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
}
