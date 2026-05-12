package dev.harrypulvirenti.fire2mqtt.mqtt

import android.util.Log
import com.hivemq.client.mqtt.MqttGlobalPublishFilter
import com.hivemq.client.mqtt.datatypes.MqttQos
import com.hivemq.client.mqtt.mqtt5.Mqtt5AsyncClient
import com.hivemq.client.mqtt.mqtt5.Mqtt5Client
import com.hivemq.client.mqtt.mqtt5.message.publish.Mqtt5Publish
import com.hivemq.client.mqtt.mqtt5.message.publish.Mqtt5WillPublish
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.UUID

private const val TAG = "Fire2MQTT/MqttClient"

data class MqttConfig(
    val host: String,
    val port: Int = 1883,
    val username: String? = null,
    val password: String? = null,
    val clientId: String = "fire2mqtt_${UUID.randomUUID()}",
    val willTopic: String,
    val willPayload: String = "offline",
    val prefix: String,
    val deviceId: String,
)

class Fire2MqttClient(private val config: MqttConfig) {

    private var client: Mqtt5AsyncClient? = null

    fun connect(): Boolean {
        return try {
            val builder = Mqtt5Client.builder()
                .identifier(config.clientId)
                .serverHost(config.host)
                .serverPort(config.port)
                .willPublish(
                    Mqtt5WillPublish.builder()
                        .topic(config.willTopic)
                        .payload(config.willPayload.toByteArray())
                        .qos(MqttQos.AT_LEAST_ONCE)
                        .retain(true)
                        .build()
                )

            if (config.username != null) {
                builder.simpleAuth()
                    .username(config.username)
                    .password(config.password?.toByteArray())
                    .applySimpleAuth()
            }

            client = builder.buildAsync()
            client!!.connectWith()
                .cleanStart(false)
                .send()
                .get()
            Log.i(TAG, "Connected to ${config.host}:${config.port}")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Connection failed: ${e.message}")
            false
        }
    }

    fun disconnect() {
        client?.disconnectWith()
            ?.sessionExpiryInterval(0)
            ?.send()
        client = null
    }

    fun publish(topic: String, payload: String, retain: Boolean = false) {
        client?.publishWith()
            ?.topic(topic)
            ?.payload(payload.toByteArray(StandardCharsets.UTF_8))
            ?.qos(MqttQos.AT_LEAST_ONCE)
            ?.retain(retain)
            ?.send()
            ?: Log.w(TAG, "Publish attempted while disconnected: $topic")
    }

    fun incomingMessages(): Flow<Pair<String, String>> = callbackFlow {
        val c = client ?: run { close(); return@callbackFlow }
        c.publishes(MqttGlobalPublishFilter.ALL) { msg: Mqtt5Publish ->
            val topic = msg.topic.toString()
            val payload = msg.payload.map { buf: ByteBuffer ->
                StandardCharsets.UTF_8.decode(buf).toString()
            }.orElse("")
            trySend(topic to payload)
        }
        awaitClose { /* client disconnect clears callbacks */ }
    }

    fun subscribe(vararg topics: String) {
        topics.forEach { topic ->
            client?.subscribeWith()
                ?.topicFilter(topic)
                ?.qos(MqttQos.AT_LEAST_ONCE)
                ?.send()
        }
    }
}
