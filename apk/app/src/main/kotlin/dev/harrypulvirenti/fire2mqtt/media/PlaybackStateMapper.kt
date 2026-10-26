package dev.harrypulvirenti.fire2mqtt.media

import android.media.session.PlaybackState
import dev.harrypulvirenti.fire2mqtt.mqtt.PlaybackPayload

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

    /**
     * The position *now*, extrapolated from a PlaybackState snapshot. `PlaybackState.position`
     * is the position at `lastPositionUpdateTime` (elapsedRealtime clock), which can be minutes
     * old; HA pairs `position_ms` with `ts` (now), so the raw value made the position lag.
     * Only advances while actually playing, and never past [durationMs].
     */
    fun currentPositionMs(
        positionMs: Long,
        lastUpdateElapsedMs: Long,
        nowElapsedMs: Long,
        speed: Float,
        androidState: Int,
        durationMs: Long?,
    ): Long {
        if (androidState != PlaybackState.STATE_PLAYING || lastUpdateElapsedMs <= 0) return positionMs
        val advanced = positionMs + ((nowElapsedMs - lastUpdateElapsedMs).coerceAtLeast(0) * speed).toLong()
        return if (durationMs != null) advanced.coerceAtMost(durationMs) else advanced
    }

    /**
     * Restamps a payload to [nowMs], advancing `position_ms` by the time elapsed while playing, so
     * a re-emit (e.g. only `audio_state` changed) never carries a stale `ts` and its position still
     * matches. Assumes 1x speed, which the payload doesn't carry.
     */
    fun restamp(payload: PlaybackPayload, nowMs: Long): PlaybackPayload {
        val position = payload.positionMs
        val advanced = if (payload.mediaSessionState == 3 && position != null) {
            val moved = position + (nowMs - payload.ts).coerceAtLeast(0)
            payload.durationMs?.let { moved.coerceAtMost(it) } ?: moved
        } else {
            position
        }
        return payload.copy(positionMs = advanced, ts = nowMs)
    }
}
