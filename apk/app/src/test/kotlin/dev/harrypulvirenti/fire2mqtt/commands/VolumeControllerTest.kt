package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.media.AudioManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

private const val MAX_VOLUME = 15

class VolumeControllerTest {

    private lateinit var audioManager: AudioManager
    private lateinit var controller: VolumeController

    @BeforeEach
    fun setUp() {
        audioManager = mockk(relaxed = true)
        every { audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC) } returns MAX_VOLUME
        val context = mockk<Context> {
            every { getSystemService(AudioManager::class.java) } returns audioManager
        }
        controller = VolumeController(context)
    }

    @Test fun `set within range calls setStreamVolume with exact value`() {
        controller.set(5)
        verify { audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, 5, 0) }
    }

    @Test fun `set below zero clamps to 0`() {
        controller.set(-1)
        verify { audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, 0, 0) }
    }

    @Test fun `set above max clamps to max`() {
        controller.set(999)
        verify { audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, MAX_VOLUME, 0) }
    }

    @Test fun `set at boundary 0 is accepted`() {
        controller.set(0)
        verify { audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, 0, 0) }
    }

    @Test fun `set at boundary max is accepted`() {
        controller.set(MAX_VOLUME)
        verify { audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, MAX_VOLUME, 0) }
    }

    @Test fun `stepUp calls adjustStreamVolume with ADJUST_RAISE`() {
        controller.stepUp()
        verify { audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, 0) }
    }

    @Test fun `stepDown calls adjustStreamVolume with ADJUST_LOWER`() {
        controller.stepDown()
        verify { audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, 0) }
    }

    @Test fun `mute calls adjustStreamVolume with ADJUST_MUTE`() {
        controller.mute()
        verify { audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0) }
    }

    @Test fun `unmute calls adjustStreamVolume with ADJUST_UNMUTE`() {
        controller.unmute()
        verify { audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, 0) }
    }
}
