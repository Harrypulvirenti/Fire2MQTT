package dev.harrypulvirenti.fire2mqtt.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.border
import androidx.compose.foundation.focusable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttPalette
import dev.harrypulvirenti.fire2mqtt.ui.theme.Fire2MqttTheme

/**
 * Applies the ember focus visual to any composable:
 *  - 2.5dp ember border ring when focused
 *  - scale-up animation (1.032× by default from FocusTokens)
 *  - outer ember glow via shadow elevation + ambientColor/spotColor
 *  - unfocused state shows [baseBorder]
 *
 * Pattern: pair with [Modifier.onFocusChanged] + [Modifier.focusable] on the
 * container, or use the [focusGlow] overload that takes a [focused] bool driven
 * by [MutableInteractionSource.collectIsFocusedAsState].
 */
fun Modifier.focusGlow(
    focused: Boolean,
    shape: Shape,
    baseBorder: Color,
    glowColor: Color = Fire2MqttPalette.Ember,
    ringWidth: Dp = 2.5.dp,
    focusScale: Float = 1.032f,
): Modifier = this
    .graphicsLayer {
        val target = if (focused) focusScale else 1f
        scaleX = target
        scaleY = target
    }
    .then(
        if (focused) {
            Modifier
                .shadow(
                    elevation = 24.dp,
                    shape = shape,
                    ambientColor = glowColor.copy(alpha = 0.34f),
                    spotColor = glowColor.copy(alpha = 0.34f),
                )
                .border(width = ringWidth, color = glowColor, shape = shape)
        } else {
            Modifier.border(width = 1.dp, color = baseBorder, shape = shape)
        }
    )

/**
 * A fully self-contained focus modifier that wires its own [MutableInteractionSource]
 * and [focusable], then applies [focusGlow]. Use this on any leaf item.
 *
 * Returns the [MutableInteractionSource] so callers can observe clicks etc.
 *
 * Usage:
 * ```
 * val interactionSource = remember { MutableInteractionSource() }
 * Box(
 *     modifier = Modifier
 *         .selfFocusGlow(shape = RoundedCornerShape(15.dp), baseBorder = colors.line)
 *         .focusable(interactionSource = interactionSource)
 *         .clickable(interactionSource = interactionSource, indication = null) { ... }
 * )
 * ```
 *
 * Actually the simplest pattern is to accept [focused] externally (from onFocusChanged)
 * and call [focusGlow] — see [focusGlow] above. This file purposely keeps it thin.
 */

/**
 * Convenience composed modifier: manages its own [MutableInteractionSource], reads
 * focus state, animates scale, and draws the ring + glow — all in one call.
 * The caller still needs to add [Modifier.focusable] AFTER this (so the focus node
 * exists). Example:
 *
 * ```kotlin
 * Box(
 *     modifier = Modifier
 *         .animatedFocusGlow(shape = cardShape, baseBorder = colors.line)
 *         .focusable()
 * )
 * ```
 */
fun Modifier.animatedFocusGlow(
    shape: Shape = RectangleShape,
    baseBorder: Color = Fire2MqttPalette.Line,
    glowColor: Color = Fire2MqttPalette.Ember,
): Modifier = composed {
    val interactionSource = remember { MutableInteractionSource() }
    val focused by interactionSource.collectIsFocusedAsState()

    val focusTokens = Fire2MqttTheme.focus
    val scale by animateFloatAsState(
        targetValue = if (focused) focusTokens.scale else 1f,
        animationSpec = tween(durationMillis = 170),
        label = "focusScale",
    )

    this
        .graphicsLayer {
            scaleX = scale
            scaleY = scale
        }
        .then(
            if (focused) {
                Modifier
                    .shadow(
                        elevation = 24.dp,
                        shape = shape,
                        ambientColor = glowColor.copy(alpha = 0.34f),
                        spotColor = glowColor.copy(alpha = 0.34f),
                    )
                    .border(width = focusTokens.ringWidth, color = glowColor, shape = shape)
            } else {
                Modifier.border(width = 1.dp, color = baseBorder, shape = shape)
            }
        )
        .focusable(interactionSource = interactionSource)
}
