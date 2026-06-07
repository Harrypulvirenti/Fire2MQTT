package dev.harrypulvirenti.fire2mqtt.data

import android.content.Context
import org.koin.core.annotation.Single

/**
 * Typed wrapper over SharedPreferences, using the same name/mode that
 * PreferenceManager.getDefaultSharedPreferences() used historically, so existing
 * installs don't lose their settings after the migration away from SettingsActivity.
 *
 * Key names and defaults are frozen — the running service and prior installs depend on them.
 */
@Single
class SettingsRepository(private val context: Context) {

    private val prefs = context.getSharedPreferences(
        "${context.packageName}_preferences",
        Context.MODE_PRIVATE,
    )

    data class MqttSettings(
        val host: String,
        val port: Int,
        val username: String,
        val password: String,
        val deviceId: String,
        val topicPrefix: String,
    )

    fun load(): MqttSettings = MqttSettings(
        host        = prefs.getString(KEY_HOST, DEFAULT_HOST) ?: DEFAULT_HOST,
        port        = prefs.getString(KEY_PORT, DEFAULT_PORT_STR)?.toIntOrNull() ?: DEFAULT_PORT,
        username    = prefs.getString(KEY_USERNAME, DEFAULT_USERNAME) ?: DEFAULT_USERNAME,
        password    = prefs.getString(KEY_PASSWORD, DEFAULT_PASSWORD) ?: DEFAULT_PASSWORD,
        deviceId    = prefs.getString(KEY_DEVICE_ID, DEFAULT_DEVICE_ID) ?: DEFAULT_DEVICE_ID,
        topicPrefix = prefs.getString(KEY_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX) ?: DEFAULT_TOPIC_PREFIX,
    )

    fun setHost(value: String) {
        prefs.edit().putString(KEY_HOST, value).apply()
    }

    /** Port is persisted as a String to preserve the string-typed key used historically. */
    fun setPort(value: Int) {
        prefs.edit().putString(KEY_PORT, value.toString()).apply()
    }

    fun setUsername(value: String) {
        prefs.edit().putString(KEY_USERNAME, value).apply()
    }

    fun setPassword(value: String) {
        prefs.edit().putString(KEY_PASSWORD, value).apply()
    }

    fun setDeviceId(value: String) {
        prefs.edit().putString(KEY_DEVICE_ID, value).apply()
    }

    fun setTopicPrefix(value: String) {
        prefs.edit().putString(KEY_TOPIC_PREFIX, value).apply()
    }

    companion object {
        /** Matches the name used by PreferenceManager.getDefaultSharedPreferences(). */
        const val PREFS_NAME_SUFFIX = "_preferences"

        private const val KEY_HOST         = "broker_host"
        private const val KEY_PORT         = "broker_port"
        private const val KEY_USERNAME     = "broker_username"
        private const val KEY_PASSWORD     = "broker_password"
        private const val KEY_DEVICE_ID    = "device_id"
        private const val KEY_TOPIC_PREFIX = "topic_prefix"

        private const val DEFAULT_HOST         = ""
        private const val DEFAULT_PORT_STR     = "1883"
        private const val DEFAULT_PORT         = 1883
        private const val DEFAULT_USERNAME     = ""
        private const val DEFAULT_PASSWORD     = ""
        private const val DEFAULT_DEVICE_ID    = "fire_tv"
        private const val DEFAULT_TOPIC_PREFIX = "fire2mqtt"
    }
}
