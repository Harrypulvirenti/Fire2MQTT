package dev.harrypulvirenti.fire2mqtt.system

import android.content.Intent
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ScreenWatcherTest {

    private val awake = ScreenState(on = true, dreaming = false)
    private val dreaming = ScreenState(on = true, dreaming = true)
    private val off = ScreenState(on = false, dreaming = false)

    @Test fun `dream start keeps the screen on and marks dreaming`() {
        assertEquals(dreaming, ScreenWatcher.next(awake, Intent.ACTION_DREAMING_STARTED))
    }

    @Test fun `dream stop clears dreaming and keeps the screen on`() {
        assertEquals(awake, ScreenWatcher.next(dreaming, Intent.ACTION_DREAMING_STOPPED))
    }

    @Test fun `screen off ends the dream`() {
        assertEquals(off, ScreenWatcher.next(dreaming, Intent.ACTION_SCREEN_OFF))
    }

    @Test fun `screen on leaves dreaming untouched`() {
        assertEquals(awake, ScreenWatcher.next(off, Intent.ACTION_SCREEN_ON))
    }

    @Test fun `unknown action changes nothing`() {
        assertEquals(dreaming, ScreenWatcher.next(dreaming, "something.else"))
    }
}
