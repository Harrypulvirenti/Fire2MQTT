package dev.harrypulvirenti.fire2mqtt.system

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.PowerManager
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import org.koin.core.annotation.Factory

/**
 * [on] mirrors PowerManager.isInteractive, which stays true while the screensaver runs.
 * [dreaming] is whether the screensaver (an Android dream) is up: on Fire TV it doesn't change
 * the foreground app, so this is the only signal that it started or ended.
 */
data class ScreenState(val on: Boolean, val dreaming: Boolean)

@Factory
class ScreenWatcher(private val context: Context) {

    fun screenStateFlow(): Flow<ScreenState> = callbackFlow {
        val pm = context.getSystemService(PowerManager::class.java)
        // No public API reports a dream already running, so start from "not dreaming"; the
        // broadcasts below correct it on the next start/stop.
        var state = ScreenState(on = pm.isInteractive, dreaming = false)
        trySend(state)

        val receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context, intent: Intent) {
                state = next(state, intent.action)
                trySend(state)
            }
        }
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_DREAMING_STARTED)
            addAction(Intent.ACTION_DREAMING_STOPPED)
        }
        context.registerReceiver(receiver, filter)
        awaitClose { context.unregisterReceiver(receiver) }
    }.distinctUntilChanged()

    companion object {
        /** State after the broadcast [action]. Pure for testing. */
        internal fun next(state: ScreenState, action: String?): ScreenState = when (action) {
            Intent.ACTION_SCREEN_ON -> state.copy(on = true)
            // A dream can't outlive the screen going off.
            Intent.ACTION_SCREEN_OFF -> ScreenState(on = false, dreaming = false)
            Intent.ACTION_DREAMING_STARTED -> ScreenState(on = true, dreaming = true)
            Intent.ACTION_DREAMING_STOPPED -> state.copy(dreaming = false)
            else -> state
        }
    }
}
