package dev.harrypulvirenti.fire2mqtt.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.materialIcon
import androidx.compose.material.icons.materialPath
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.State
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.focus.focusProperties
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.harrypulvirenti.fire2mqtt.R
import dev.harrypulvirenti.fire2mqtt.ui.ConnState
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttTheme
import dev.harrypulvirenti.fire2mqtt.ui.theme.JetBrainsMono

/* ─────────────────────────────────────────────────────────────────────────
 * Shared focus surface
 * ──────────────────────────────────────────────────────────────────────── */

/**
 * Animated focus scale for [tvFocus]. Hoisted out of the modifier factory so
 * tvFocus stays a plain (non-composable) Modifier builder, per the Compose API
 * guidelines on modifier factories.
 */
@Composable
fun animateTvFocusScale(focused: Boolean): State<Float> = animateFloatAsState(
    targetValue = if (focused) Fire2MqttTheme.focus.scale else 1f,
    animationSpec = tween(170),
    label = "focusScale",
)

/**
 * The canonical TV focus visual: animated scale-up + ember ring + outer glow when
 * [focused], a hairline border otherwise. Pair with a [MutableInteractionSource]
 * fed into [clickable]/[focusable]/[BasicTextField] so [focused] tracks D-pad focus.
 *
 * [scale] is a provider (from [animateTvFocusScale]) read inside the graphics
 * layer, so animation frames update the layer without recomposing the caller.
 */
fun Modifier.tvFocus(
    focused: Boolean,
    scale: () -> Float,
    shape: Shape,
    bg: Color,
    baseBorder: Color,
    ring: Color,
    ringWidth: Dp,
): Modifier = this
    .graphicsLayer { scaleX = scale(); scaleY = scale() }
    .then(
        if (focused) Modifier.shadow(
            elevation = 30.dp,
            shape = shape,
            ambientColor = ring.copy(alpha = .55f),
            spotColor = ring.copy(alpha = .65f),
        ) else Modifier
    )
    .clip(shape)
    .background(bg, shape)
    .border(
        width = if (focused) ringWidth else 1.dp,
        color = if (focused) ring else baseBorder,
        shape = shape,
    )

private val fieldShape = RoundedCornerShape(15.dp)
val cardShape = RoundedCornerShape(22.dp)

/* ─────────────────────────────────────────────────────────────────────────
 * Eyebrow / card
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun Eyebrow(label: String, modifier: Modifier = Modifier) {
    val c = Fire2MqttTheme.colors
    Row(verticalAlignment = Alignment.CenterVertically, modifier = modifier) {
        Box(
            Modifier
                .size(11.dp)
                .shadow(8.dp, RoundedCornerShape(3.dp), spotColor = c.ember)
                .background(c.ember, RoundedCornerShape(3.dp))
        )
        Spacer(Modifier.width(12.dp))
        Text(label.uppercase(), color = c.text3, style = Fire2MqttTheme.type.eyebrow)
    }
}

@Composable
fun Card(
    modifier: Modifier = Modifier,
    content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit,
) {
    val c = Fire2MqttTheme.colors
    Column(
        modifier
            .clip(cardShape)
            .background(c.surface, cardShape)
            .border(1.dp, c.line, cardShape)
            .padding(horizontal = 22.dp, vertical = 20.dp),
        content = content,
    )
}

/* ─────────────────────────────────────────────────────────────────────────
 * Header (brand mark + wordmark + global status badge)
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun BrandMark() {
    val c = Fire2MqttTheme.colors
    Box(
        Modifier
            .size(56.dp)
            .shadow(18.dp, RoundedCornerShape(16.dp), spotColor = c.ember)
            .background(
                Brush.linearGradient(listOf(c.ember2, c.ember, Color(0xFFE85A06))),
                RoundedCornerShape(16.dp),
            ),
        contentAlignment = Alignment.BottomCenter,
    ) {
        Row(
            Modifier.padding(bottom = 15.dp),
            horizontalArrangement = Arrangement.spacedBy(5.dp),
            verticalAlignment = Alignment.Bottom,
        ) {
            listOf(11.dp, 18.dp, 27.dp).forEach { h ->
                Box(
                    Modifier
                        .width(6.dp)
                        .height(h)
                        .background(c.emberInk, RoundedCornerShape(3.dp))
                )
            }
        }
    }
}

@Composable
fun Header(connection: ConnState, isRunning: Boolean) {
    val c = Fire2MqttTheme.colors
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            BrandMark()
            Spacer(Modifier.width(18.dp))
            Column {
                Row {
                    Text("Fire", color = c.text, style = Fire2MqttTheme.type.wordmark)
                    Text("2", color = c.ember, style = Fire2MqttTheme.type.wordmark,
                        fontWeight = FontWeight.ExtraBold)
                    Text("MQTT", color = c.text, style = Fire2MqttTheme.type.wordmark)
                }
                Spacer(Modifier.height(6.dp))
                Text(
                    stringResource(R.string.brand_tagline).uppercase(),
                    color = c.text3, style = Fire2MqttTheme.type.tagline,
                )
            }
        }
        GlobalStatusBadge(connection, isRunning)
    }
}

@Composable
private fun GlobalStatusBadge(connection: ConnState, isRunning: Boolean) {
    val c = Fire2MqttTheme.colors
    val (label, color) = when {
        isRunning || connection == ConnState.Running -> stringResource(R.string.status_running) to c.green
        connection == ConnState.Connected -> stringResource(R.string.status_connected) to c.green
        connection == ConnState.Testing -> stringResource(R.string.status_testing) to c.amber
        else -> stringResource(R.string.status_disconnected) to c.text3
    }
    Row(
        Modifier
            .clip(CircleShape)
            .background(Color(0x4D000000), CircleShape)
            .border(1.dp, c.line2, CircleShape)
            .padding(horizontal = 22.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(13.dp).background(color, CircleShape))
        Spacer(Modifier.width(13.dp))
        Text(label.uppercase(), color = color, style = Fire2MqttTheme.type.badge)
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Editable field rows — D-pad focus shows the ring only; pressing select flips
 * the field editable and shows the system IME (no keyboard pop on navigation).
 * A single readOnly-gated BasicTextField keeps focus stable on the remote.
 * ──────────────────────────────────────────────────────────────────────── */

/** Modifier that toggles [editingState] on select/back while the field is focused. */
private fun Modifier.editToggle(
    editing: Boolean,
    setEditing: (Boolean) -> Unit,
    hideKeyboard: () -> Unit,
): Modifier = this.onPreviewKeyEvent { e ->
    if (e.type != KeyEventType.KeyDown) return@onPreviewKeyEvent false
    when (e.key) {
        Key.DirectionCenter, Key.Enter, Key.NumPadEnter ->
            if (!editing) { setEditing(true); true } else false
        Key.Back ->
            if (editing) { setEditing(false); hideKeyboard(); true } else false
        else -> false
    }
}

@Composable
fun FieldRow(
    label: String,
    hint: String?,
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    optional: Boolean = false,
    password: Boolean = false,
) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusScale by animateTvFocusScale(focused)
    val keyboard = LocalSoftwareKeyboardController.current
    var editing by remember { mutableStateOf(false) }
    LaunchedEffect(editing) { if (editing) keyboard?.show() }

    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        readOnly = !editing,
        textStyle = Fire2MqttTheme.type.value.copy(color = c.text, textAlign = TextAlign.End),
        cursorBrush = SolidColor(c.ember),
        interactionSource = interaction,
        keyboardOptions = KeyboardOptions(
            keyboardType = if (password) KeyboardType.Password else KeyboardType.Text,
            imeAction = ImeAction.Done,
        ),
        keyboardActions = KeyboardActions(onDone = { editing = false; keyboard?.hide() }),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        modifier = modifier
            .fillMaxWidth()
            .tvFocus(focused, { focusScale }, fieldShape,
                if (focused) c.surface3 else c.surface2, c.line,
                c.ember, Fire2MqttTheme.focus.ringWidth)
            .editToggle(editing, { editing = it }, { keyboard?.hide() })
            .onFocusChanged { if (!it.isFocused) editing = false }
            .padding(horizontal = 22.dp, vertical = 15.dp),
        decorationBox = { inner ->
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.width(200.dp)) {
                    Text(label, color = c.text, style = Fire2MqttTheme.type.label, maxLines = 1)
                    if (hint != null) {
                        Spacer(Modifier.height(3.dp))
                        Text(hint.uppercase(), color = c.text4,
                            style = Fire2MqttTheme.type.hint, maxLines = 1)
                    }
                }
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterEnd) {
                    if (value.isEmpty()) {
                        Text(
                            if (optional) stringResource(R.string.field_value_optional) else placeholder,
                            color = c.text4, style = Fire2MqttTheme.type.value,
                            maxLines = 1, textAlign = TextAlign.End,
                        )
                    }
                    inner()
                }
                Spacer(Modifier.width(16.dp))
                EditPip(focused)
            }
        },
    )
}

/** Compact 2-up editable field (Username/Password, Device ID/Topic Prefix). */
@Composable
fun CompactField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    optional: Boolean = false,
    password: Boolean = false,
) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusScale by animateTvFocusScale(focused)
    val keyboard = LocalSoftwareKeyboardController.current
    var editing by remember { mutableStateOf(false) }
    LaunchedEffect(editing) { if (editing) keyboard?.show() }

    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        readOnly = !editing,
        textStyle = Fire2MqttTheme.type.valueSmall.copy(color = c.text),
        cursorBrush = SolidColor(c.ember),
        interactionSource = interaction,
        keyboardOptions = KeyboardOptions(
            keyboardType = if (password) KeyboardType.Password else KeyboardType.Text,
            imeAction = ImeAction.Done,
        ),
        keyboardActions = KeyboardActions(onDone = { editing = false; keyboard?.hide() }),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        modifier = modifier
            .fillMaxWidth()
            .tvFocus(focused, { focusScale }, fieldShape,
                if (focused) c.surface3 else c.surface2, c.line,
                c.ember, Fire2MqttTheme.focus.ringWidth)
            .editToggle(editing, { editing = it }, { keyboard?.hide() })
            .onFocusChanged { if (!it.isFocused) editing = false }
            .padding(horizontal = 18.dp, vertical = 14.dp),
        decorationBox = { inner ->
            Column {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(label, color = c.text, style = Fire2MqttTheme.type.labelSmall,
                            maxLines = 1)
                        if (optional) {
                            Spacer(Modifier.width(8.dp))
                            Text(stringResource(R.string.field_optional_tag), color = c.text4,
                                style = Fire2MqttTheme.type.hint)
                        }
                    }
                    EditPip(focused)
                }
                Spacer(Modifier.height(8.dp))
                Box {
                    if (value.isEmpty()) {
                        Text(stringResource(R.string.field_value_optional), color = c.text4,
                            style = Fire2MqttTheme.type.valueSmall, maxLines = 1)
                    }
                    inner()
                }
            }
        },
    )
}

@Composable
private fun EditPip(focused: Boolean) {
    val c = Fire2MqttTheme.colors
    Box(
        Modifier
            .size(38.dp)
            .clip(RoundedCornerShape(11.dp))
            .border(1.dp, if (focused) c.ember.copy(alpha = .5f) else c.line2, RoundedCornerShape(11.dp)),
        contentAlignment = Alignment.Center,
    ) {
        Text("✎", color = if (focused) c.ember else c.text3, fontSize = 17.sp,
            fontFamily = JetBrainsMono)
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Port stepper — SELECT to activate, then D-pad left/right adjusts the value.
 * While inactive, left/right pass through so focus can move off the field.
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun PortStepper(value: Int, onChange: (Int) -> Unit, modifier: Modifier = Modifier) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusScale by animateTvFocusScale(focused)
    var active by remember { mutableStateOf(false) }
    // Leaving the field (focus lost) always exits edit mode.
    LaunchedEffect(focused) { if (!focused) active = false }
    fun step(d: Int) = onChange((value + d).coerceIn(1, 65535))

    Row(
        modifier
            .fillMaxWidth()
            .onPreviewKeyEvent { e ->
                if (e.type != KeyEventType.KeyDown) return@onPreviewKeyEvent false
                when (e.key) {
                    Key.DirectionCenter, Key.Enter, Key.NumPadEnter -> { active = !active; true }
                    Key.Back -> if (active) { active = false; true } else false
                    Key.DirectionLeft -> if (active) { step(-1); true } else false
                    Key.DirectionRight -> if (active) { step(1); true } else false
                    else -> false
                }
            }
            .tvFocus(focused, { focusScale }, fieldShape,
                if (active) c.surface3 else c.surface2,
                if (active) c.ember.copy(alpha = .6f) else c.line,
                c.ember, Fire2MqttTheme.focus.ringWidth)
            .clickable(interaction, indication = null, role = Role.Button) { active = !active }
            .padding(horizontal = 22.dp, vertical = 15.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(stringResource(R.string.field_port), color = c.text,
                style = Fire2MqttTheme.type.label)
            Spacer(Modifier.height(3.dp))
            val hint = if (active) stringResource(R.string.field_port_adjust_hint)
                       else stringResource(R.string.field_port_hint)
            Text(hint.uppercase(), color = if (active) c.ember2 else c.text4,
                style = Fire2MqttTheme.type.hint)
        }
        StepBtn("–", active) { step(-1) }
        Spacer(Modifier.width(16.dp))
        Text("$value", color = if (active) c.ember2 else c.text,
            style = Fire2MqttTheme.type.stepperValue)
        Spacer(Modifier.width(16.dp))
        StepBtn("+", active) { step(1) }
    }
}

@Composable
private fun StepBtn(glyph: String, active: Boolean, onClick: () -> Unit) {
    val c = Fire2MqttTheme.colors
    Box(
        Modifier
            .size(40.dp)
            .clip(RoundedCornerShape(11.dp))
            .background(Color(0x40000000), RoundedCornerShape(11.dp))
            .border(1.dp, if (active) c.ember.copy(alpha = .45f) else c.line2, RoundedCornerShape(11.dp))
            // Not a D-pad stop: the stepper row's key handler owns ±; this stays
            // clickable for pointer/talkback without adding an extra focus target.
            .focusProperties { canFocus = false }
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(glyph, color = if (active) c.ember2 else c.text2, fontSize = 24.sp,
            fontFamily = JetBrainsMono)
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * TLS toggle — SELECT flips mqtts on/off. Mirrors PortStepper's focus styling.
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun TlsToggle(checked: Boolean, onCheckedChange: (Boolean) -> Unit, modifier: Modifier = Modifier) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusScale by animateTvFocusScale(focused)

    Row(
        modifier
            .fillMaxWidth()
            .onPreviewKeyEvent { e ->
                if (e.type != KeyEventType.KeyDown) return@onPreviewKeyEvent false
                when (e.key) {
                    Key.DirectionCenter, Key.Enter, Key.NumPadEnter -> { onCheckedChange(!checked); true }
                    else -> false
                }
            }
            .tvFocus(focused, { focusScale }, fieldShape, c.surface2, c.line, c.ember,
                Fire2MqttTheme.focus.ringWidth)
            .clickable(interaction, indication = null, role = Role.Switch) { onCheckedChange(!checked) }
            .padding(horizontal = 22.dp, vertical = 15.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(stringResource(R.string.field_use_tls), color = c.text,
                style = Fire2MqttTheme.type.label)
            Spacer(Modifier.height(3.dp))
            Text(stringResource(R.string.field_use_tls_hint).uppercase(), color = c.text4,
                style = Fire2MqttTheme.type.hint)
        }
        Box(
            Modifier
                .clip(RoundedCornerShape(11.dp))
                .background(
                    if (checked) c.green.copy(alpha = .18f) else Color(0x40000000),
                    RoundedCornerShape(11.dp),
                )
                .border(1.dp, if (checked) c.green.copy(alpha = .5f) else c.line2,
                    RoundedCornerShape(11.dp))
                .padding(horizontal = 18.dp, vertical = 9.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                if (checked) stringResource(R.string.toggle_on) else stringResource(R.string.toggle_off),
                color = if (checked) c.green else c.text3,
                style = Fire2MqttTheme.type.label,
            )
        }
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Topic preview + deferred QR card
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun TopicPreview(prefix: String, deviceId: String) {
    val c = Fire2MqttTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Color(0x38000000), RoundedCornerShape(14.dp))
            .border(1.dp, c.line2, RoundedCornerShape(14.dp))
            .padding(horizontal = 22.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(stringResource(R.string.topic_publishes_to).uppercase(), color = c.text4,
            style = Fire2MqttTheme.type.caption)
        Spacer(Modifier.width(16.dp))
        Row {
            Text(prefix.ifBlank { stringResource(R.string.topic_default_prefix) }, color = c.ember2,
                style = Fire2MqttTheme.type.itemEmphasis)
            Text("/", color = c.text2, style = Fire2MqttTheme.type.itemBody)
            Text(deviceId.ifBlank { stringResource(R.string.topic_default_device) }, color = c.ember2,
                style = Fire2MqttTheme.type.itemEmphasis)
            Text(stringResource(R.string.topic_state_suffix), color = c.text2,
                style = Fire2MqttTheme.type.itemBody)
        }
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Connection panel + buttons
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun ConnectionStatus(connection: ConnState, message: String) {
    val c = Fire2MqttTheme.colors
    val (label, color) = when (connection) {
        ConnState.Running -> stringResource(R.string.conn_running) to c.green
        ConnState.Connected -> stringResource(R.string.conn_connected) to c.green
        ConnState.Testing -> stringResource(R.string.conn_testing) to c.amber
        ConnState.Failed -> stringResource(R.string.conn_failed) to c.red
        ConnState.Disconnected -> stringResource(R.string.conn_disconnected) to c.text2
    }
    Column(Modifier.padding(vertical = 6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(18.dp).background(color, CircleShape))
            Spacer(Modifier.width(16.dp))
            Text(label, color = color, style = Fire2MqttTheme.type.statusTitle)
        }
        Spacer(Modifier.height(8.dp))
        Text(message, color = c.text3, style = Fire2MqttTheme.type.itemBody)
    }
}

@Composable
fun SecondaryButton(text: String, testing: Boolean, onClick: () -> Unit) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val focusScale by animateTvFocusScale(focused)
    Row(
        Modifier
            .fillMaxWidth()
            .tvFocus(focused, { focusScale }, fieldShape, c.surface2, c.line2,
                c.ember, Fire2MqttTheme.focus.ringWidth)
            .clickable(interaction, indication = null, role = Role.Button, onClick = onClick)
            .padding(vertical = 18.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (testing) {
            CircularProgressIndicator(Modifier.size(20.dp), color = c.text, strokeWidth = 3.dp)
            Spacer(Modifier.width(14.dp))
        }
        Text(text, color = c.text, style = Fire2MqttTheme.type.button)
    }
}

@Composable
fun PrimaryButton(text: String, enabled: Boolean, onClick: () -> Unit) {
    val c = Fire2MqttTheme.colors
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val bg = if (enabled)
        Brush.verticalGradient(listOf(Color(0xFFFF8C2E), c.ember))
    else Brush.verticalGradient(listOf(c.surface2, c.surface2))
    val scale by animateTvFocusScale(focused && enabled)
    Row(
        Modifier
            .fillMaxWidth()
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .then(
                if (focused && enabled) Modifier.shadow(28.dp, fieldShape, spotColor = c.ember)
                else Modifier
            )
            .clip(fieldShape)
            .background(bg, fieldShape)
            .border(
                if (focused && enabled) Fire2MqttTheme.focus.ringWidth else 1.dp,
                if (focused && enabled) c.ember else c.line,
                fieldShape,
            )
            .clickable(interaction, indication = null, enabled = enabled, role = Role.Button, onClick = onClick)
            .padding(vertical = 18.dp),
        horizontalArrangement = Arrangement.Center,
    ) {
        Text(text, color = if (enabled) c.emberInk else c.text3,
            style = Fire2MqttTheme.type.buttonPrimary)
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Permissions
 * ──────────────────────────────────────────────────────────────────────── */

enum class PermIcon { Notif, Access }

/**
 * Material's Filled.Accessibility, inlined verbatim so we don't depend on
 * material-icons-extended for a single glyph (Check/Notifications come from icons-core).
 */
private val AccessibilityIcon: ImageVector by lazy {
    materialIcon(name = "Filled.Accessibility") {
        materialPath {
            moveTo(12.0f, 2.0f)
            curveToRelative(1.1f, 0.0f, 2.0f, 0.9f, 2.0f, 2.0f)
            reflectiveCurveToRelative(-0.9f, 2.0f, -2.0f, 2.0f)
            reflectiveCurveToRelative(-2.0f, -0.9f, -2.0f, -2.0f)
            reflectiveCurveToRelative(0.9f, -2.0f, 2.0f, -2.0f)
            close()
            moveTo(21.0f, 9.0f)
            horizontalLineToRelative(-6.0f)
            verticalLineToRelative(13.0f)
            horizontalLineToRelative(-2.0f)
            verticalLineToRelative(-6.0f)
            horizontalLineToRelative(-2.0f)
            verticalLineToRelative(6.0f)
            horizontalLineTo(9.0f)
            verticalLineTo(9.0f)
            horizontalLineTo(3.0f)
            verticalLineTo(7.0f)
            horizontalLineToRelative(18.0f)
            verticalLineToRelative(2.0f)
            close()
        }
    }
}

private fun PermIcon.vector(): ImageVector = when (this) {
    PermIcon.Notif -> Icons.Filled.Notifications
    PermIcon.Access -> AccessibilityIcon
}

/** Non-actionable status row: green when the access is enabled, dim "Pending" otherwise. */
@Composable
fun PermissionRow(icon: PermIcon, name: String, desc: String, enabled: Boolean) {
    val c = Fire2MqttTheme.colors
    val rowBg = if (enabled) c.green.copy(alpha = .07f) else c.surface2
    val rowBorder = if (enabled) c.green.copy(alpha = .2f) else c.line

    Row(
        Modifier
            .fillMaxWidth()
            .clip(fieldShape)
            .background(rowBg, fieldShape)
            .border(1.dp, rowBorder, fieldShape)
            .padding(horizontal = 20.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier
                .size(46.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(if (enabled) c.green.copy(alpha = .12f) else Color(0x40000000), RoundedCornerShape(12.dp))
                .border(1.dp, if (enabled) c.green.copy(alpha = .35f) else c.line2, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon.vector(), null, tint = if (enabled) c.green else c.text3,
                modifier = Modifier.size(22.dp))
        }
        Spacer(Modifier.width(16.dp))
        Column(Modifier.weight(1f)) {
            Text(name, color = c.text, style = Fire2MqttTheme.type.label)
            Spacer(Modifier.height(4.dp))
            Text(desc, color = c.text3, style = Fire2MqttTheme.type.bodySmall,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Spacer(Modifier.width(12.dp))
        if (enabled) {
            Row(
                Modifier
                    .clip(CircleShape)
                    .background(c.green.copy(alpha = .16f), CircleShape)
                    .padding(horizontal = 18.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Filled.Check, null, tint = c.green, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(10.dp))
                Text(stringResource(R.string.perm_enabled), color = c.green,
                    style = Fire2MqttTheme.type.itemEmphasis)
            }
        } else {
            Text(stringResource(R.string.perm_pending), color = c.text4,
                style = Fire2MqttTheme.type.itemEmphasis)
        }
    }
}

/**
 * One-time setup card shown until WRITE_SECURE_SETTINGS is held: explains the single ADB
 * grant and shows the exact command (with this device's IP), plus a focusable Re-check button.
 */
@Composable
fun AdbSetupCard(ip: String, onRecheck: () -> Unit) {
    val c = Fire2MqttTheme.colors
    Column(
        Modifier
            .fillMaxWidth()
            .clip(fieldShape)
            .background(c.ember.copy(alpha = .06f), fieldShape)
            .border(1.dp, c.ember.copy(alpha = .25f), fieldShape)
            .padding(20.dp),
    ) {
        Text(stringResource(R.string.adb_setup_title), color = c.ember2,
            style = Fire2MqttTheme.type.badge)
        Spacer(Modifier.height(8.dp))
        Text(stringResource(R.string.adb_setup_body), color = c.text2,
            style = Fire2MqttTheme.type.body)
        Spacer(Modifier.height(12.dp))
        Text(
            stringResource(R.string.adb_command, ip),
            color = c.text, style = Fire2MqttTheme.type.body,
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .background(Color(0x40000000), RoundedCornerShape(10.dp))
                .border(1.dp, c.line2, RoundedCornerShape(10.dp))
                .padding(horizontal = 16.dp, vertical = 12.dp),
        )
        Spacer(Modifier.height(14.dp))
        SecondaryButton(stringResource(R.string.perm_recheck), testing = false, onClick = onRecheck)
    }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Hint bar
 * ──────────────────────────────────────────────────────────────────────── */

@Composable
fun HintBar() {
    val c = Fire2MqttTheme.colors
    Row(
        Modifier.fillMaxWidth().padding(top = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Keycaps(listOf("↑", "↓", "←", "→")); Spacer(Modifier.width(11.dp))
        Hint(stringResource(R.string.hint_navigate)); Spacer(Modifier.width(28.dp))
        Keycaps(listOf("⏎")); Spacer(Modifier.width(11.dp))
        Hint(stringResource(R.string.hint_select)); Spacer(Modifier.width(28.dp))
        Keycaps(listOf("esc")); Spacer(Modifier.width(11.dp))
        Hint(stringResource(R.string.hint_back))
        Spacer(Modifier.weight(1f))
        Text(stringResource(R.string.hint_footer).uppercase(), color = c.text4,
            style = Fire2MqttTheme.type.caption)
    }
}

@Composable
private fun Hint(text: String) {
    Text(text, color = Fire2MqttTheme.colors.text3, style = Fire2MqttTheme.type.body)
}

@Composable
private fun Keycaps(caps: List<String>) {
    val c = Fire2MqttTheme.colors
    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        caps.forEach { cap ->
            Box(
                Modifier
                    .height(30.dp)
                    .widthForCap(cap)
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0x4D000000), RoundedCornerShape(8.dp))
                    .border(1.dp, c.line2, RoundedCornerShape(8.dp))
                    .padding(horizontal = 8.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(cap, color = c.text2, style = Fire2MqttTheme.type.body)
            }
        }
    }
}

private fun Modifier.widthForCap(cap: String): Modifier =
    if (cap.length > 1) this.width(46.dp) else this.width(30.dp)

/* ─────────────────────────────────────────────────────────────────────────
 * TV design canvas — lays the UI out on a fixed-width logical canvas by
 * overriding LocalDensity so 1 dp = (screen width / designWidthDp) px. Unlike a
 * graphicsLayer scale this lays out in real pixels, so it fills the screen
 * edge-to-edge with no letterbox and crisp text, on any TV resolution.
 *
 * The canvas is 1550 design-dp wide: the 1920×1080 design was authored at that
 * logical width so everything renders ~1.24× larger — TV ten-foot sizing.
 *
 * Tradeoff (deliberate): inside this scope dp values no longer match device dp,
 * so anything that assumes physical density (system-inset conversions, minimum
 * touch-target enforcement) would be off. Acceptable for a TV-only, D-pad app.
 * ──────────────────────────────────────────────────────────────────────── */
@Composable
fun TvDesignScale(designWidthDp: Float = 1550f, content: @Composable () -> Unit) {
    val c = Fire2MqttTheme.colors
    val config = androidx.compose.ui.platform.LocalConfiguration.current
    val base = androidx.compose.ui.platform.LocalDensity.current
    val screenWidthPx = config.screenWidthDp * base.density
    val targetDensity = (screenWidthPx / designWidthDp).coerceAtLeast(0.1f)
    androidx.compose.runtime.CompositionLocalProvider(
        androidx.compose.ui.platform.LocalDensity provides
            androidx.compose.ui.unit.Density(targetDensity, base.fontScale),
    ) {
        Box(Modifier.fillMaxSize().background(c.bgLetter)) { content() }
    }
}
