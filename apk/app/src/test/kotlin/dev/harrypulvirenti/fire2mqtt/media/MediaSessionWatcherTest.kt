package dev.harrypulvirenti.fire2mqtt.media

import android.media.MediaMetadata
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

    private fun meta(vararg pairs: Pair<String, String>): (String) -> String? = mapOf(*pairs)::get

    @Test fun `title prefers TITLE and falls back to DISPLAY_TITLE`() {
        assertEquals("T", MediaSessionWatcher.titleFrom(meta(
            MediaMetadata.METADATA_KEY_TITLE to "T",
            MediaMetadata.METADATA_KEY_DISPLAY_TITLE to "D",
        )))
        assertEquals("D", MediaSessionWatcher.titleFrom(meta(
            MediaMetadata.METADATA_KEY_TITLE to " ",
            MediaMetadata.METADATA_KEY_DISPLAY_TITLE to "D",
        )))
        assertNull(MediaSessionWatcher.titleFrom(meta()))
    }

    @Test fun `artist falls back to album artist then display subtitle`() {
        assertEquals("A", MediaSessionWatcher.artistFrom(meta(
            MediaMetadata.METADATA_KEY_ARTIST to "A",
            MediaMetadata.METADATA_KEY_DISPLAY_SUBTITLE to "S",
        )))
        assertEquals("AA", MediaSessionWatcher.artistFrom(meta(
            MediaMetadata.METADATA_KEY_ALBUM_ARTIST to "AA",
            MediaMetadata.METADATA_KEY_DISPLAY_SUBTITLE to "S",
        )))
        assertEquals("The Series", MediaSessionWatcher.artistFrom(meta(
            MediaMetadata.METADATA_KEY_TITLE to "The Episode",
            MediaMetadata.METADATA_KEY_DISPLAY_SUBTITLE to "The Series",
        )))
    }

    @Test fun `display subtitle that repeats the title is not used as artist`() {
        assertNull(MediaSessionWatcher.artistFrom(meta(
            MediaMetadata.METADATA_KEY_DISPLAY_TITLE to "Same",
            MediaMetadata.METADATA_KEY_DISPLAY_SUBTITLE to "Same",
        )))
    }
}
