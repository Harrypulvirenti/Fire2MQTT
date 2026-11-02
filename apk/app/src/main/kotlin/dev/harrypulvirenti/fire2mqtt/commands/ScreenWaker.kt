package dev.harrypulvirenti.fire2mqtt.commands

import android.content.Context
import android.os.PowerManager
import co.touchlab.kermit.Logger
import org.koin.core.annotation.Factory

private val logger = Logger.withTag("Fire2MQTT/ScreenWaker")

// Long enough for the framework to act on the wake-up; the lock releases itself after this.
private const val WAKE_LOCK_TIMEOUT_MS = 1_000L

/**
 * Turns the screen on, ending the screensaver if one is running.
 *
 * Fire TV's screensaver (full-screen ads, photo slideshow) is an Android dream drawn above every
 * activity, so an app launched from Home Assistant starts behind it: its audio plays but the
 * screensaver stays on screen. A screen wake lock with ACQUIRE_CAUSES_WAKEUP moves the device
 * from dreaming (or asleep) to awake, which dismisses the dream. Needs only the normal WAKE_LOCK
 * permission, so it works where the accessibility service is refused (Fire OS 6.7).
 */
@Factory
class ScreenWaker(private val context: Context) {

    @Suppress("DEPRECATION") // Still the only app-level way to wake the device on Fire OS.
    fun wake() {
        runCatching {
            val pm = context.getSystemService(PowerManager::class.java)
            pm.newWakeLock(
                PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
                "Fire2MQTT:wake",
            ).acquire(WAKE_LOCK_TIMEOUT_MS)
        }.onSuccess { logger.i { "Woke the screen" } }
            .onFailure { logger.e(it) { "Could not wake the screen: ${it.message}" } }
    }
}
