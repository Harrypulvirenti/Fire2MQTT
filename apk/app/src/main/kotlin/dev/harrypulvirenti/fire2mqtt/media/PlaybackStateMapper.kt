package dev.harrypulvirenti.fire2mqtt.media

import android.media.session.PlaybackState

/** Maps Android PlaybackState.STATE_* integers to Fire2MQTT schema integers.
 *
 * The schema ints deliberately match python-androidtv's media_session_state convention:
 *   0 = None/unknown, 1 = STOPPED, 2 = PAUSED, 3 = PLAYING
 */
object PlaybackStateMapper {

    fun toSchemaInt(androidState: Int): Int = when (androidState) {
        PlaybackState.STATE_PLAYING,
        PlaybackState.STATE_BUFFERING,
        PlaybackState.STATE_FAST_FORWARDING,
        PlaybackState.STATE_REWINDING,
        PlaybackState.STATE_SKIPPING_TO_NEXT,
        PlaybackState.STATE_SKIPPING_TO_PREVIOUS,
        PlaybackState.STATE_SKIPPING_TO_QUEUE_ITEM -> 3

        PlaybackState.STATE_PAUSED -> 2

        PlaybackState.STATE_STOPPED,
        PlaybackState.STATE_ERROR -> 1

        else -> 0
    }
}
