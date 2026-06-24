package dev.harrypulvirenti.fire2mqtt.media

import android.media.session.MediaController
import android.media.session.PlaybackState
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class MediaSessionWatcherTest {

    private fun controller(state: Int, pkg: String): MediaController {
        val ps = mockk<PlaybackState> { every { this@mockk.state } returns state }
        return mockk { every { playbackState } returns ps; every { packageName } returns pkg }
    }

    @Test fun `playing foreground session wins over a background none session`() {
        // The real Crunchyroll bug: Alexa/Vizzini sit at STATE_NONE and used to clobber it.
        val crunchyroll = controller(PlaybackState.STATE_PLAYING, "com.crunchyroll.crunchyroid")
        val alexa = controller(PlaybackState.STATE_NONE, "com.amazon.alexamediaplayer")
        val vizzini = controller(PlaybackState.STATE_NONE, "com.amazon.vizzini")

        val primary = MediaSessionWatcher.selectPrimary(listOf(alexa, vizzini, crunchyroll))

        assertEquals("com.crunchyroll.crunchyroid", primary?.packageName)
    }

    @Test fun `playing outranks paused`() {
        val playing = controller(PlaybackState.STATE_PLAYING, "a")
        val paused = controller(PlaybackState.STATE_PAUSED, "b")
        assertEquals("a", MediaSessionWatcher.selectPrimary(listOf(paused, playing))?.packageName)
    }

    @Test fun `no sessions selects nothing`() {
        assertNull(MediaSessionWatcher.selectPrimary(emptyList()))
    }

    @Test fun `state priority ranks playing above paused above stopped above none`() {
        assertTrue(
            MediaSessionWatcher.statePriority(PlaybackState.STATE_PLAYING) >
                MediaSessionWatcher.statePriority(PlaybackState.STATE_PAUSED)
        )
        assertTrue(
            MediaSessionWatcher.statePriority(PlaybackState.STATE_PAUSED) >
                MediaSessionWatcher.statePriority(PlaybackState.STATE_STOPPED)
        )
        assertTrue(
            MediaSessionWatcher.statePriority(PlaybackState.STATE_STOPPED) >
                MediaSessionWatcher.statePriority(PlaybackState.STATE_NONE)
        )
    }
}
