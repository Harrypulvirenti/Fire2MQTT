package dev.harrypulvirenti.fire2mqtt.mqtt

import co.touchlab.kermit.Logger
import com.hivemq.client.mqtt.MqttGlobalPublishFilter
import com.hivemq.client.mqtt.datatypes.MqttQos
import com.hivemq.client.mqtt.mqtt5.Mqtt5AsyncClient
import com.hivemq.client.mqtt.mqtt5.Mqtt5Client
import com.hivemq.client.mqtt.mqtt5.message.publish.Mqtt5Publish
import com.hivemq.client.mqtt.mqtt5.message.publish.Mqtt5WillPublish
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.receiveAsFlow
import org.koin.core.annotation.Factory
import org.koin.core.annotation.InjectedParam
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

private val logger = Logger.withTag("Fire2MQTT/MqttClient")

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

@Factory
class Fire2MqttClient(@InjectedParam private val config: MqttConfig) {

    private var client: Mqtt5AsyncClient? = null
    private var onConnected: (() -> Unit)? = null
    // Bounded so a broker-side retained-storm or runaway publisher can't grow
    // the channel without limit. CommandRouter consumes O(1) per message and the
    // realistic command rate is well under 1/s, so 64 slots is generous; overflow
    // trips the trySend.isFailure log path in registerIncomingPublishCallback.
    private val incomingMessageChannel = Channel<Pair<String, String>>(capacity = 64)
    private val retainedCache = ConcurrentHashMap<String, ByteArray>()
    // Serializes retained publish + replay so a concurrent republishRetained()
    // can't overwrite a fresh watcher payload with an older cached one on the
    // broker. The lock is held only across an in-memory cache write and a
    // HiveMQ send() enqueue, both sub-ms.
    private val retainedLock = ReentrantLock()

    fun setOnConnected(callback: () -> Unit) {
        onConnected = callback
    }

    fun connect(): Boolean {
        var newClient: Mqtt5AsyncClient? = null
        return try {
            val builder = Mqtt5Client.builder()
                .identifier(config.clientId)
                .serverHost(config.host)
                .serverPort(config.port)
                .automaticReconnectWithDefaultConfig()
                .addConnectedListener { onConnected?.invoke() }
                .addDisconnectedListener { ctx ->
                    logger.w { "Disconnected from broker: ${ctx.cause.message}; auto-reconnect armed" }
                }
                .willPublish(
                    Mqtt5WillPublish.builder()
                        .topic(config.willTopic)
                        .payload(config.willPayload.toByteArray())
                        .qos(MqttQos.AT_LEAST_ONCE)
                        .retain(true)
                        .build()
                )

            if (config.username != null) {
                val auth = builder.simpleAuth().username(config.username)
                config.password?.let { auth.password(it.toByteArray()) }
                auth.applySimpleAuth()
            }

            newClient = builder.buildAsync()
            client = newClient
            registerIncomingPublishCallback(newClient)
            newClient.connectWith()
                .cleanStart(false)
                .send()
                .get()
            logger.i { "Connected to ${config.host}:${config.port}" }
            true
        } catch (e: Exception) {
            runCatching {
                newClient?.disconnectWith()
                    ?.sessionExpiryInterval(0)
                    ?.send()
                    ?.get()
            }
            if (client === newClient) {
                client = null
            }
            logger.e(e) { "Connection failed: ${e.message}" }
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
        val bytes = payload.toByteArray(StandardCharsets.UTF_8)
        if (retain) {
            // Cache write and broker enqueue happen under the same lock as
            // republishRetained() to keep on-wire order matching call order;
            // otherwise replay could re-send a stale cached payload after a
            // newer live publish.
            retainedLock.withLock {
                retainedCache[topic] = bytes
                val c = client ?: return  // pre-connect seed: cache only, no send
                c.publishWith()
                    .topic(topic)
                    .payload(bytes)
                    .qos(MqttQos.AT_LEAST_ONCE)
                    .retain(true)
                    .send()
            }
            return
        }
        val c = client
        if (c == null) {
            logger.w { "Publish dropped (disconnected, non-retained): $topic" }
            return
        }
        c.publishWith()
            .topic(topic)
            .payload(bytes)
            .qos(MqttQos.AT_LEAST_ONCE)
            .retain(false)
            .send()
    }

    fun republishRetained() {
        retainedLock.withLock {
            val c = client ?: return
            retainedCache.forEach { (topic, bytes) ->
                c.publishWith()
                    .topic(topic)
                    .payload(bytes)
                    .qos(MqttQos.AT_LEAST_ONCE)
                    .retain(true)
                    .send()
            }
        }
    }

    fun incomingMessages(): Flow<Pair<String, String>> = incomingMessageChannel.receiveAsFlow()

    private fun registerIncomingPublishCallback(client: Mqtt5AsyncClient) {
        client.publishes(MqttGlobalPublishFilter.ALL) { msg: Mqtt5Publish ->
            val topic = msg.topic.toString()
            val payload = msg.payload.map { buf: ByteBuffer ->
                StandardCharsets.UTF_8.decode(buf).toString()
            }.orElse("")
            val result = incomingMessageChannel.trySend(topic to payload)
            if (result.isFailure) {
                logger.w { "Incoming MQTT message dropped: $topic" }
            }
        }
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
