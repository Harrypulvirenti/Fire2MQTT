package dev.harrypulvirenti.fire2mqtt.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Devices
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material3.Text
import androidx.compose.ui.text.font.FontWeight
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.ui.components.AdbSetupCard
import dev.harrypulvirenti.fire2mqtt.ui.components.Card
import dev.harrypulvirenti.fire2mqtt.ui.components.CompactField
import dev.harrypulvirenti.fire2mqtt.ui.components.ConnectionStatus
import dev.harrypulvirenti.fire2mqtt.ui.components.Eyebrow
import dev.harrypulvirenti.fire2mqtt.ui.components.FieldRow
import dev.harrypulvirenti.fire2mqtt.ui.components.Header
import dev.harrypulvirenti.fire2mqtt.ui.components.HintBar
import dev.harrypulvirenti.fire2mqtt.ui.components.PermIcon
import dev.harrypulvirenti.fire2mqtt.ui.components.PermissionRow
import dev.harrypulvirenti.fire2mqtt.ui.components.PortStepper
import dev.harrypulvirenti.fire2mqtt.ui.components.PrimaryButton
import dev.harrypulvirenti.fire2mqtt.ui.components.SecondaryButton
import dev.harrypulvirenti.fire2mqtt.ui.components.TopicPreview
import dev.harrypulvirenti.fire2mqtt.ui.components.TvDesignScale
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttTheme
import dev.harrypulvirenti.fire2mqtt.ui.theme.JetBrainsMono

@Composable
fun SetupDashboard(
    state: SetupUiState,
    onHostChange: (String) -> Unit = {},
    onPortChange: (Int) -> Unit = {},
    onUsernameChange: (String) -> Unit = {},
    onPasswordChange: (String) -> Unit = {},
    onDeviceIdChange: (String) -> Unit = {},
    onTopicPrefixChange: (String) -> Unit = {},
    onTestConnection: () -> Unit = {},
    onStartService: () -> Unit = {},
    onStopService: () -> Unit = {},
    onRecheck: () -> Unit = {},
) {
    val c = Fire2MqttTheme.colors
    val hostFocus = remember { FocusRequester() }

    // Initial focus lands on the Host field so the remote always has a target.
    LaunchedEffect(Unit) { runCatching { hostFocus.requestFocus() } }

    Box(
        Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    colors = listOf(c.ember.copy(alpha = .10f), c.bg, c.bgLetter),
                    center = Offset(300f, 0f),
                    radius = 1600f,
                )
            )
            .padding(horizontal = Fire2MqttTheme.focus.safeX, vertical = Fire2MqttTheme.focus.safeY),
    ) {
        Column(Modifier.fillMaxSize()) {
            Header(state.connection, state.isServiceRunning)
            Spacer(Modifier.height(20.dp))

            Row(Modifier.weight(1f).fillMaxWidth()) {
                // LEFT — configuration
                Column(
                    Modifier.weight(1.32f).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Card {
                        Eyebrow(stringResource(R.string.card_mqtt_broker))
                        Spacer(Modifier.height(14.dp))
                        Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
                            FieldRow(
                                label = stringResource(R.string.field_host),
                                hint = stringResource(R.string.field_host_hint),
                                value = state.host, onValueChange = onHostChange,
                                placeholder = stringResource(R.string.field_host_placeholder),
                                modifier = Modifier.focusRequester(hostFocus),
                            )
                            PortStepper(state.port, onPortChange)
                            Row(horizontalArrangement = Arrangement.spacedBy(11.dp)) {
                                CompactField(stringResource(R.string.field_username), state.username,
                                    onUsernameChange, Modifier.weight(1f), optional = true)
                                CompactField(stringResource(R.string.field_password), state.password,
                                    onPasswordChange, Modifier.weight(1f), optional = true, password = true)
                            }
                        }
                    }
                    Card {
                        Eyebrow(stringResource(R.string.card_device_identity))
                        Spacer(Modifier.height(14.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(11.dp)) {
                            CompactField(stringResource(R.string.field_device_id), state.deviceId,
                                onDeviceIdChange, Modifier.weight(1f))
                            CompactField(stringResource(R.string.field_topic_prefix), state.topicPrefix,
                                onTopicPrefixChange, Modifier.weight(1f))
                        }
                        Spacer(Modifier.height(12.dp))
                        TopicPreview(state.topicPrefix, state.deviceId)
                    }
                }

                Spacer(Modifier.width(24.dp))

                // RIGHT — status + permissions
                Column(
                    Modifier.weight(1f).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Card {
                        Eyebrow(stringResource(R.string.card_connection))
                        Spacer(Modifier.height(8.dp))
                        ConnectionStatus(state.connection, state.connectionMessage.resolve())
                        Spacer(Modifier.height(14.dp))
                        SecondaryButton(
                            text = if (state.connection == ConnState.Testing)
                                stringResource(R.string.btn_test_connection_testing)
                            else stringResource(R.string.btn_test_connection),
                            testing = state.connection == ConnState.Testing,
                            onClick = onTestConnection,
                        )
                        Spacer(Modifier.height(14.dp))
                        PrimaryButton(
                            text = if (state.isServiceRunning) stringResource(R.string.btn_stop_service)
                            else stringResource(R.string.btn_start_service),
                            enabled = state.isServiceRunning || state.canStart,
                            onClick = { if (state.isServiceRunning) onStopService() else onStartService() },
                        )
                        if (!state.canStart && !state.isServiceRunning) {
                            Spacer(Modifier.height(12.dp))
                            Text(
                                if (state.connection != ConnState.Connected)
                                    stringResource(R.string.helper_test_to_enable)
                                else stringResource(R.string.helper_grant_to_enable),
                                color = c.text4, fontFamily = JetBrainsMono, fontSize = 15.sp,
                                modifier = Modifier.fillMaxWidth(),
                                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                            )
                        }
                    }
                    Card {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Eyebrow(stringResource(R.string.card_permissions))
                            Row {
                                Text("${state.perms.grantedCount}", color = c.green,
                                    fontFamily = JetBrainsMono, fontWeight = FontWeight.SemiBold, fontSize = 17.sp)
                                Text(" ${stringResource(R.string.perm_count_suffix)}", color = c.text3,
                                    fontFamily = JetBrainsMono, fontWeight = FontWeight.SemiBold, fontSize = 17.sp)
                            }
                        }
                        Spacer(Modifier.height(14.dp))
                        Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
                            // One-time ADB grant gate — shown until WRITE_SECURE_SETTINGS is held.
                            if (!state.writeSecureSettings) {
                                AdbSetupCard(state.adbIp, onRecheck = onRecheck)
                            }
                            PermissionRow(PermIcon.Access,
                                stringResource(R.string.perm_access_name),
                                stringResource(R.string.perm_access_desc),
                                state.perms.accessibility)
                            PermissionRow(PermIcon.Notif,
                                stringResource(R.string.perm_notif_name),
                                stringResource(R.string.perm_notif_desc),
                                state.perms.notification)
                        }
                    }
                }
            }

            HintBar()
        }
    }
}

/* ── Preview ──────────────────────────────────────────────────────────── */

/** Configured + running: green badge, both permissions enabled, WSS held. */
private fun previewConfiguredState() = SetupUiState(
    host = "192.168.1.42", port = 1883,
    username = "homeassistant", password = "mqttpass",
    deviceId = "living_room_tv", topicPrefix = "fire2mqtt",
    connection = ConnState.Running,
    connectionMessage = TextValue.TextResource(R.string.msg_publishing),
    perms = Perms(accessibility = true, notification = true),
    writeSecureSettings = true,
    isServiceRunning = true,
)

/** First run: nothing configured, no permissions, WSS not yet granted (ADB card shown). */
private fun previewFirstRunState() = SetupUiState(
    connection = ConnState.Disconnected,
    connectionMessage = TextValue.TextResource(R.string.msg_no_broker),
    writeSecureSettings = false,
    adbIp = "192.168.1.50",
)

@Preview(name = "Configured · 1080p", device = Devices.TV_1080p)
@Composable
private fun SetupDashboardConfiguredPreview() {
    Fire2MqttTheme { TvDesignScale { SetupDashboard(previewConfiguredState()) } }
}

@Preview(name = "First run · 1080p", device = Devices.TV_1080p)
@Composable
private fun SetupDashboardFirstRunPreview() {
    Fire2MqttTheme { TvDesignScale { SetupDashboard(previewFirstRunState()) } }
}

@Preview(name = "Italian · 1080p", device = Devices.TV_1080p, locale = "it")
@Composable
private fun SetupDashboardItalianPreview() {
    Fire2MqttTheme { TvDesignScale { SetupDashboard(previewConfiguredState()) } }
}

@Preview(name = "German · 1080p", device = Devices.TV_1080p, locale = "de")
@Composable
private fun SetupDashboardGermanPreview() {
    Fire2MqttTheme { TvDesignScale { SetupDashboard(previewFirstRunState()) } }
}
