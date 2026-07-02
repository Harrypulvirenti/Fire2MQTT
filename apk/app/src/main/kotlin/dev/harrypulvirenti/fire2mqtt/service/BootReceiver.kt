package dev.harrypulvirenti.fire2mqtt.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import co.touchlab.kermit.Logger
import dev.harrypulvirenti.fire2mqtt.system.SecureSettingsManager

private val logger = Logger.withTag("Fire2MQTT/Boot")

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        if (action in listOf(
                Intent.ACTION_BOOT_COMPLETED,
                Intent.ACTION_MY_PACKAGE_REPLACED,
            )
        ) {
            // Log the trigger and the notification-listener grant state so the boot/update path is
            // traceable. Pair this with the MediaSession watcher's "bound and watching" vs "not
            // bound" log: if enabledInSettings=true here but the watcher then reports not bound, the
            // OS did NOT rebind the listener on this event and an ADB re-provision is required.
            val enabledInSettings = SecureSettingsManager.isNotificationListenerEnabled(context)
            logger.i {
                "Received $action — starting Fire2MqttService " +
                    "(notification listener enabled in settings=$enabledInSettings)"
            }
            val service = Intent(context, Fire2MqttService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(service)
            } else {
                context.startService(service)
            }
        }
    }
}
