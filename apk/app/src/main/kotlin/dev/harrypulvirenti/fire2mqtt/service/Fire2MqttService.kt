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
import dev.harrypulvirenti.fire2mqtt.mqtt.AppPayload
import dev.harrypulvirenti.fire2mqtt.mqtt.BrokerHostValidator
import dev.harrypulvirenti.fire2mqtt.mqtt.DevicePayload
import dev.harrypulvirenti.fire2mqtt.mqtt.Fire2MqttClient
import dev.harrypulvirenti.fire2mqtt.mqtt.MqttConfig
import dev.harrypulvirenti.fire2mqtt.mqtt.ScreenPayload
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
    private var pipelineJob: Job? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        val previousPipeline = pipelineJob
        pipelineJob = scope.launch {
            if (previousPipeline?.isActive == true) {
                Log.d(TAG, "Pipeline already running — restarting with latest settings")
                previousPipeline.cancelAndJoin()
                mqttClient?.disconnect()
                mqttClient = null
                commandRouter = null
            }
            startPipeline()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        pipelineJob = null
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

        // Resolve and pin: hand HiveMQ a validated IP literal so its auto-reconnect
        // can't drift to a different (potentially public) DNS answer later.
        val resolvedHost = BrokerHostValidator.resolveToPrivateAddress(host)
        if (resolvedHost == null) {
            Log.e(
                TAG,
                "Broker host '$host' did not resolve to a private/LAN address (or " +
                    "had a public candidate among its answers) — refusing to connect " +
                    "over cleartext. Configure an RFC1918 IP, loopback, or link-local broker.",
            )
            stopSelf()
            return
        }

        val config = MqttConfig(
            host = resolvedHost,
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

        // Pre-seed the retained-state cache before connecting. These publishes
        // no-op the network send (client not built yet) but populate the cache
        // so the very first CONNACK can replay them via republishRetained().
        client.publish(TopicSchema.status(prefix, deviceId), "online", retain = true)
        client.publish(
            TopicSchema.stateDevice(prefix, deviceId),
            Json.encodeToString(buildDevicePayload()),
            retain = true,
        )

        // Replay every retained topic and re-issue command subscriptions on
        // every (re)connect. HiveMQ fires this on the first CONNACK and after
        // each auto-reconnect. Watcher publishes between connects update the
        // cache, so playback/app/screen/volume are restored alongside
        // status + device even when the broker lost session state.
        // MQTT 5 SUBSCRIBE is idempotent, so re-issuing is safe.
        client.setOnConnected {
            client.republishRetained()
            client.subscribe(
                TopicSchema.cmdLaunch(prefix, deviceId),
                TopicSchema.cmdKey(prefix, deviceId),
                TopicSchema.cmdVolume(prefix, deviceId),
                TopicSchema.cmdPower(prefix, deviceId),
                TopicSchema.cmdMedia(prefix, deviceId),
            )
        }

        // Initial connect with exponential backoff. HiveMQ's auto-reconnect only
        // engages after the first successful CONNACK, so we own retries until then.
        var backoffMs = 2_000L
        while (!client.connect()) {
            Log.w(TAG, "Initial broker connect failed — retrying in ${backoffMs}ms")
            delay(backoffMs)
            backoffMs = (backoffMs * 2).coerceAtMost(60_000L)
        }

        commandRouter = CommandRouter(this, prefix, deviceId)
        val mediaWatcher = MediaSessionWatcher(
            this,
            ComponentName(this, MediaNotificationListener::class.java)
        )

        // All long-lived collectors run as children of pipelineJob via coroutineScope.
        // coroutineScope suspends until every child completes; the flows are infinite
        // so pipelineJob stays active for the pipeline's lifetime, and the
        // duplicate-start guard in onStartCommand actually holds.
        coroutineScope {
            // Route incoming commands
            launch {
                client.incomingMessages().collect { (topic, payload) ->
                    commandRouter?.route(topic, payload)
                }
            }

            // MediaSession playback events
            launch {
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
            launch {
                ForegroundAppWatcher(this@Fire2MqttService).foregroundAppFlow()
                    .catch { Log.e(TAG, "ForegroundApp error: ${it.message}") }
                    .collect { event ->
                        val appJson = Json.encodeToString(
                            AppPayload(`package` = event.packageName, name = event.appName)
                        )
                        client.publish(TopicSchema.stateApp(prefix, deviceId), appJson, retain = true)
                    }
            }

            // Screen state
            launch {
                ScreenWatcher(this@Fire2MqttService).screenStateFlow()
                    .catch { Log.e(TAG, "Screen error: ${it.message}") }
                    .collect { on ->
                        val json = Json.encodeToString(ScreenPayload(on = on))
                        client.publish(TopicSchema.stateScreen(prefix, deviceId), json, retain = true)
                    }
            }

            // Volume
            launch {
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
