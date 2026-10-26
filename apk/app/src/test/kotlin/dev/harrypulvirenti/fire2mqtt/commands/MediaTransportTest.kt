package dev.harrypulvirenti.fire2mqtt.commands

import android.media.session.MediaController
import android.media.session.PlaybackState
import android.view.KeyEvent
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class MediaTransportTest {

    private fun controller(state: Int, pkg: String): MediaController {
        val ps = mockk<PlaybackState> { every { this@mockk.state } returns state }
        return mockk { every { playbackState } returns ps; every { packageName } returns pkg }
    }

    @Test fun `paused foreground app wins over an idle cast session`() {
        // The Google TV bug (finding 3 in #41): after YouTube paused, PLAY went to Cast.
        val youtube = controller(PlaybackState.STATE_PAUSED, "com.google.android.youtube.tv")
        val cast = controller(PlaybackState.STATE_NONE, "com.google.android.apps.mediashell")

        val target = MediaTransport.selectTarget(listOf(cast, youtube), "com.google.android.youtube.tv")

        assertEquals("com.google.android.youtube.tv", target?.packageName)
    }

    @Test fun `foreground session wins even when a background session is playing`() {
        val music = controller(PlaybackState.STATE_PLAYING, "com.spotify.music")
        val netflix = controller(PlaybackState.STATE_PAUSED, "com.netflix.ninja")

        val target = MediaTransport.selectTarget(listOf(music, netflix), "com.netflix.ninja")

        assertEquals("com.netflix.ninja", target?.packageName)
    }

    @Test fun `without a foreground session the most active session is used`() {
        // e.g. music playing behind the launcher
        val music = controller(PlaybackState.STATE_PLAYING, "com.spotify.music")
        val idle = controller(PlaybackState.STATE_NONE, "com.amazon.vizzini")

        val target = MediaTransport.selectTarget(listOf(idle, music), "com.amazon.tv.launcher")

        assertEquals("com.spotify.music", target?.packageName)
    }

    @Test fun `no sessions selects nothing`() {
        assertNull(MediaTransport.selectTarget(emptyList(), "com.netflix.ninja"))
    }

    @Test fun `play_pause pauses a playing session and plays a paused one`() {
        val controls = mockk<MediaController.TransportControls>(relaxed = true)

        MediaTransport.applyTo(controls, PlaybackState.STATE_PLAYING, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)
        verify { controls.pause() }

        MediaTransport.applyTo(controls, PlaybackState.STATE_PAUSED, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)
        verify { controls.play() }
    }

    @Test fun `transport keys map onto transport controls`() {
        val controls = mockk<MediaController.TransportControls>(relaxed = true)

        assertTrue(MediaTransport.applyTo(controls, null, KeyEvent.KEYCODE_MEDIA_STOP))
        assertTrue(MediaTransport.applyTo(controls, null, KeyEvent.KEYCODE_MEDIA_NEXT))
        assertTrue(MediaTransport.applyTo(controls, null, KeyEvent.KEYCODE_MEDIA_PREVIOUS))

        verify { controls.stop() }
        verify { controls.skipToNext() }
        verify { controls.skipToPrevious() }
    }

    @Test fun `non media key is not handled`() {
        val controls = mockk<MediaController.TransportControls>(relaxed = true)
        assertFalse(MediaTransport.applyTo(controls, null, KeyEvent.KEYCODE_HOME))
    }
}
