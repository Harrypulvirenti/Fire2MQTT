package dev.harrypulvirenti.fire2mqtt.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.ComponentName
import android.content.Intent
import android.net.ConnectivityManager
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import dev.harrypulvirenti.fire2mqtt.Fire2MqttApp
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.commands.CommandRouter
import dev.harrypulvirenti.fire2mqtt.media.MediaNotificationListener
import dev.harrypulvirenti.fire2mqtt.media.MediaSessionWatcher
import dev.harrypulvirenti.fire2mqtt.mqtt.DevicePayload
import dev.harrypulvirenti.fire2mqtt.mqtt.Fire2MqttClient
import dev.harrypulvirenti.fire2mqtt.mqtt.MqttConfig
import dev.harrypulvirenti.fire2mqtt.mqtt.TopicSchema
import dev.harrypulvirenti.fire2mqtt.system.ForegroundAppWatcher
import dev.harrypulvirenti.fire2mqtt.system.ScreenWatcher
import dev.harrypulvirenti.fire2mqtt.system.VolumeWatcher
import dev.harrypulvirenti.fire2mqtt.ui.SettingsActivity
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.catch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.net.NetworkInterface

private const val TAG = "Fire2MQTT/Service"
private const val NOTIFICATION_ID = 1

class Fire2MqttService : Service() {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var mqttClient: Fire2MqttClient? = null
    private var commandRouter: CommandRouter? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        scope.launch { startPipeline() }
        return START_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        mqttClient?.disconnect()
        super.onDestroy()
    }

    private suspend fun startPipeline() {
        val prefs = SettingsActivity.getPrefs(this)
        val prefix = prefs.getString("topic_prefix", "fire2mqtt") ?: "fire2mqtt"
        val deviceId = prefs.getString("device_id", "fire_tv") ?: "fire_tv"
        val host = prefs.getString("broker_host", "") ?: ""
        val port = prefs.getInt("broker_port", 1883)
        val username = prefs.getString("broker_username", null)
        val password = prefs.getString("broker_password", null)

        if (host.isBlank()) {
            Log.e(TAG, "Broker host not configured — stopping service")
            stopSelf()
            return
        }

        val config = MqttConfig(
            host = host,
            port = port,
            username = username,
            password = password,
            willTopic = TopicSchema.status(prefix, deviceId),
            willPayload = "offline",
            prefix = prefix,
            deviceId = deviceId,
        )

        val client = Fire2MqttClient(config)
        mqttClient = client

        if (!client.connect()) {
            Log.e(TAG, "Could not connect to broker — will retry on next START_STICKY")
            return
        }

        // Publish device info + online status
        client.publish(TopicSchema.status(prefix, deviceId), "online", retain = true)
        client.publish(
            TopicSchema.stateDevice(prefix, deviceId),
            Json.encodeToString(buildDevicePayload()),
            retain = true,
        )

        // Subscribe to command topics
        client.subscribe(
            TopicSchema.cmdLaunch(prefix, deviceId),
            TopicSchema.cmdKey(prefix, deviceId),
            TopicSchema.cmdVolume(prefix, deviceId),
            TopicSchema.cmdPower(prefix, deviceId),
            TopicSchema.cmdMedia(prefix, deviceId),
        )
        commandRouter = CommandRouter(this, prefix, deviceId)

        // Route incoming commands
        scope.launch {
            client.incomingMessages().collect { (topic, payload) ->
                commandRouter?.route(topic, payload)
            }
        }

        // MediaSession playback events
        val mediaWatcher = MediaSessionWatcher(
            this,
            ComponentName(this, MediaNotificationListener::class.java)
        )
        scope.launch {
            mediaWatcher.playbackEvents()
                .catch { Log.e(TAG, "MediaSession error: ${it.message}") }
                .collect { payload ->
                    client.publish(
                        TopicSchema.statePlayback(prefix, deviceId),
                        Json.encodeToString(payload),
                        retain = true,
                    )
                }
        }

        // Foreground app
        scope.launch {
            ForegroundAppWatcher(this@Fire2MqttService).foregroundAppFlow()
                .catch { Log.e(TAG, "ForegroundApp error: ${it.message}") }
                .collect { event ->
                    val appJson = """{"package":"${event.packageName}","name":"${event.appName}","ts":${System.currentTimeMillis()}}"""
                    client.publish(TopicSchema.stateApp(prefix, deviceId), appJson, retain = true)
                }
        }

        // Screen state
        scope.launch {
            ScreenWatcher(this@Fire2MqttService).screenStateFlow()
                .catch { Log.e(TAG, "Screen error: ${it.message}") }
                .collect { on ->
                    val json = """{"on":$on,"ts":${System.currentTimeMillis()}}"""
                    client.publish(TopicSchema.stateScreen(prefix, deviceId), json, retain = true)
                }
        }

        // Volume
        scope.launch {
            VolumeWatcher(this@Fire2MqttService).volumeFlow()
                .catch { Log.e(TAG, "Volume error: ${it.message}") }
                .collect { vol ->
                    client.publish(
                        TopicSchema.stateVolume(prefix, deviceId),
                        Json.encodeToString(vol),
                        retain = true,
                    )
                }
        }
    }

    private fun buildDevicePayload(): DevicePayload {
        val model = android.os.Build.MODEL
        val fireOs = android.os.Build.VERSION.RELEASE
        val ip = getLocalIpAddress()
        val mac = getMacAddress()
        return DevicePayload(model = model, fireOs = fireOs, ip = ip, mac = mac)
    }

    private fun getLocalIpAddress(): String {
        return try {
            NetworkInterface.getNetworkInterfaces().toList()
                .flatMap { it.inetAddresses.toList() }
                .firstOrNull { !it.isLoopbackAddress && it.hostAddress?.contains(':') == false }
                ?.hostAddress ?: "unknown"
        } catch (_: Exception) { "unknown" }
    }

    private fun getMacAddress(): String {
        return try {
            NetworkInterface.getNetworkInterfaces().toList()
                .firstOrNull { it.name == "wlan0" }
                ?.hardwareAddress
                ?.joinToString(":") { "%02x".format(it) }
                ?: "unknown"
        } catch (_: Exception) { "unknown" }
    }

    private fun buildNotification(): Notification {
        val intent = Intent(this, SettingsActivity::class.java)
        val pi = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)
        return NotificationCompat.Builder(this, Fire2MqttApp.SERVICE_CHANNEL_ID)
            .setContentTitle("Fire2MQTT")
            .setContentText("Publishing to MQTT broker")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
    }
}
