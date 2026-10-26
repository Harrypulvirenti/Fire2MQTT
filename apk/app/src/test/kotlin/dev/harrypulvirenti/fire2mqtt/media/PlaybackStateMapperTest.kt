package dev.harrypulvirenti.fire2mqtt.media

import android.media.session.PlaybackState
import dev.harrypulvirenti.fire2mqtt.mqtt.PlaybackPayload
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.Arguments
import org.junit.jupiter.params.provider.MethodSource
import org.junit.jupiter.params.provider.ValueSource
import java.util.stream.Stream

class PlaybackStateMapperTest {

    @ParameterizedTest
    @MethodSource("playingStates")
    fun `active playback states map to 3`(state: Int) {
        assertEquals(3, PlaybackStateMapper.toSchemaInt(state))
    }

    @ParameterizedTest
    @MethodSource("stoppedStates")
    fun `stopped and error states map to 1`(state: Int) {
        assertEquals(1, PlaybackStateMapper.toSchemaInt(state))
    }

    @ParameterizedTest
    @ValueSource(ints = [PlaybackState.STATE_NONE, -1, 999])
    fun `unknown states map to 0`(state: Int) {
        assertEquals(0, PlaybackStateMapper.toSchemaInt(state))
    }

    @ParameterizedTest
    @ValueSource(ints = [PlaybackState.STATE_PAUSED])
    fun `paused maps to 2`(state: Int) {
        assertEquals(2, PlaybackStateMapper.toSchemaInt(state))
    }

    // --- position extrapolation (HA pairs position_ms with ts) ---

    @Test fun `playing position advances by elapsed time and speed`() {
        val pos = PlaybackStateMapper.currentPositionMs(
            positionMs = 10_000, lastUpdateElapsedMs = 1_000, nowElapsedMs = 6_000,
            speed = 1f, androidState = PlaybackState.STATE_PLAYING, durationMs = null,
        )
        assertEquals(15_000, pos)
    }

    @Test fun `paused position does not advance`() {
        val pos = PlaybackStateMapper.currentPositionMs(
            positionMs = 10_000, lastUpdateElapsedMs = 1_000, nowElapsedMs = 60_000,
            speed = 1f, androidState = PlaybackState.STATE_PAUSED, durationMs = null,
        )
        assertEquals(10_000, pos)
    }

    @Test fun `extrapolated position never passes the duration`() {
        val pos = PlaybackStateMapper.currentPositionMs(
            positionMs = 10_000, lastUpdateElapsedMs = 1_000, nowElapsedMs = 600_000,
            speed = 1f, androidState = PlaybackState.STATE_PLAYING, durationMs = 20_000,
        )
        assertEquals(20_000, pos)
    }

    @Test fun `restamp refreshes ts and advances a playing position`() {
        // The #41 burst: audio_state flips re-emitted the old payload with its old ts.
        val old = PlaybackPayload(mediaSessionState = 3, positionMs = 1_000, durationMs = 9_000, ts = 100_000)
        val restamped = PlaybackStateMapper.restamp(old, nowMs = 103_000)
        assertEquals(103_000, restamped.ts)
        assertEquals(4_000L, restamped.positionMs)
    }

    @Test fun `restamp keeps a paused position`() {
        val old = PlaybackPayload(mediaSessionState = 2, positionMs = 1_000, ts = 100_000)
        val restamped = PlaybackStateMapper.restamp(old, nowMs = 160_000)
        assertEquals(160_000, restamped.ts)
        assertEquals(1_000L, restamped.positionMs)
    }

    companion object {
        @JvmStatic
        fun playingStates(): Stream<Arguments> = Stream.of(
            Arguments.of(PlaybackState.STATE_PLAYING),
            Arguments.of(PlaybackState.STATE_BUFFERING),
            Arguments.of(PlaybackState.STATE_FAST_FORWARDING),
            Arguments.of(PlaybackState.STATE_REWINDING),
            Arguments.of(PlaybackState.STATE_SKIPPING_TO_NEXT),
            Arguments.of(PlaybackState.STATE_SKIPPING_TO_PREVIOUS),
            Arguments.of(PlaybackState.STATE_SKIPPING_TO_QUEUE_ITEM),
        )

        @JvmStatic
        fun stoppedStates(): Stream<Arguments> = Stream.of(
            Arguments.of(PlaybackState.STATE_STOPPED),
            Arguments.of(PlaybackState.STATE_ERROR),
        )
    }
}
