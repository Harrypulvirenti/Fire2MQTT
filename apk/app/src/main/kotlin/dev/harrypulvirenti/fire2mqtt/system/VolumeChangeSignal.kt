package dev.harrypulvirenti.fire2mqtt.system

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import org.koin.core.annotation.Single

/**
 * Tells [VolumeWatcher] to republish `state/volume` after the app changed the volume itself.
 *
 * The watcher's own triggers (Settings.System changes, VOLUME_CHANGED_ACTION) don't fire on
 * every device — on Google TV a volume command left HA showing the old level — so the volume
 * command path pings this signal after acting. A singleton so the controller and the watcher
 * share one instance.
 */
@Single
class VolumeChangeSignal {
    private val changes = MutableSharedFlow<Unit>(extraBufferCapacity = 1)

    val events: SharedFlow<Unit> = changes.asSharedFlow()

    fun notifyChanged() {
        changes.tryEmit(Unit)
    }
}
