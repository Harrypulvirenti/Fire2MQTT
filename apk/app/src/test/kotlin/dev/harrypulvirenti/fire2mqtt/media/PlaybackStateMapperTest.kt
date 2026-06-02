package dev.harrypulvirenti.fire2mqtt.media

import android.media.session.PlaybackState
import org.junit.jupiter.api.Assertions.assertEquals
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
