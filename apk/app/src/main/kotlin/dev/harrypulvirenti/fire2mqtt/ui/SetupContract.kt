package dev.harrypulvirenti.fire2mqtt.ui

/**
 * The frozen state contract between the setup UI (Compose) and its logic (SetupViewModel).
 *
 * The UI is a pure function of [SetupUiState] and emits events through plain lambdas
 * hoisted from the ViewModel (see SetupDashboard's parameters). Keeping the screen
 * stateless lets it render in @Preview with no-op lambdas and no Android dependencies.
 */

/** Live connection / service status, driving the status panel + global badge. */
enum class ConnState { Disconnected, Testing, Connected, Failed, Running }

/**
 * Permission state. On Fire OS the app self-enables Accessibility + Notification-listener
 * access via WRITE_SECURE_SETTINGS (see SecureSettingsManager) — these two are all that's
 * needed (foreground detection runs on the accessibility service; Usage Access was dropped).
 */
data class Perms(
    val accessibility: Boolean = false,
    val notification: Boolean = false,
) {
    val grantedCount: Int = listOf(accessibility, notification).count { it }
    val allGranted: Boolean = accessibility && notification
}

data class SetupUiState(
    val host: String = "",
    val port: Int = 1883,
    val username: String = "",
    val password: String = "",
    val deviceId: String = "fire_tv",
    val topicPrefix: String = "fire2mqtt",
    val connection: ConnState = ConnState.Disconnected,
    /** Human-readable status subline, e.g. "Connected to 192.168.1.42:1883." */
    val connectionMessage: String = "No broker configured yet.",
    val perms: Perms = Perms(),
    /** Whether WRITE_SECURE_SETTINGS is held — the one-time ADB grant that unlocks self-enable. */
    val writeSecureSettings: Boolean = false,
    /** This device's LAN IP, shown in the one-time ADB command. */
    val adbIp: String = "",
    val isServiceRunning: Boolean = false,
    /** False until the off-thread initial load completes; gates the launch splash. */
    val ready: Boolean = false,
) {
    /** Start Service is enabled only when reachable AND both permissions are enabled. */
    val canStart: Boolean
        get() = (connection == ConnState.Connected || connection == ConnState.Running) &&
            perms.allGranted
}
