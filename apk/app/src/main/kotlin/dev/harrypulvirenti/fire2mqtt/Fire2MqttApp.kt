package dev.harrypulvirenti.fire2mqtt

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build

class Fire2MqttApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                SERVICE_CHANNEL_ID,
                "Fire2MQTT Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps the Fire2MQTT background service running"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java)
                .createNotificationChannel(channel)
        }
    }

    companion object {
        const val SERVICE_CHANNEL_ID = "fire2mqtt_service"
    }
}
