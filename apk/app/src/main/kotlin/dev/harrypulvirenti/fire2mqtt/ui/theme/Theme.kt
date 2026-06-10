package dev.harrypulvirenti.fire2mqtt.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Design system surface for the whole app. Components read tokens from
 * [LocalFire2MqttColors] / [LocalFocusTokens] rather than Material's scheme,
 * but we still install a dark [MaterialTheme] so stray Material widgets inherit
 * sane defaults.
 */
@Immutable
data class Fire2MqttColors(
    val bgLetter: Color = Fire2MqttPalette.BgLetter,
    val bg: Color = Fire2MqttPalette.Bg,
    val surface: Color = Fire2MqttPalette.Surface,
    val surface2: Color = Fire2MqttPalette.Surface2,
    val surface3: Color = Fire2MqttPalette.Surface3,
    val line: Color = Fire2MqttPalette.Line,
    val line2: Color = Fire2MqttPalette.Line2,
    val text: Color = Fire2MqttPalette.Text,
    val text2: Color = Fire2MqttPalette.Text2,
    val text3: Color = Fire2MqttPalette.Text3,
    val text4: Color = Fire2MqttPalette.Text4,
    val ember: Color = Fire2MqttPalette.Ember,
    val ember2: Color = Fire2MqttPalette.Ember2,
    val emberInk: Color = Fire2MqttPalette.EmberInk,
    val green: Color = Fire2MqttPalette.Green,
    val amber: Color = Fire2MqttPalette.Amber,
    val red: Color = Fire2MqttPalette.Red,
)

/** Focus visual dynamics (the heart of the TV UI). Maps the design's --focus-* vars. */
@Immutable
data class FocusTokens(
    val scale: Float = 1.032f,
    val ringWidth: Dp = 2.5.dp,
    val lift: Dp = (-2).dp,
    val cardRadius: Dp = 22.dp,
    val fieldRadius: Dp = 15.dp,
    // ~2% overscan-safe inset on the 1920×1080 design canvas.
    val safeX: Dp = 40.dp,
    val safeY: Dp = 24.dp,
)

val LocalFire2MqttColors = staticCompositionLocalOf { Fire2MqttColors() }
val LocalFocusTokens = staticCompositionLocalOf { FocusTokens() }

/** Convenience accessor: `Fire2MqttTheme.colors.ember`, `Fire2MqttTheme.type.label`. */
object Fire2MqttTheme {
    val colors: Fire2MqttColors
        @Composable get() = LocalFire2MqttColors.current
    val focus: FocusTokens
        @Composable get() = LocalFocusTokens.current
    val fonts get() = JetBrainsMono
    val type get() = Fire2MqttType
}

@Composable
fun Fire2MqttTheme(content: @Composable () -> Unit) {
    val colors = Fire2MqttColors()
    val focus = FocusTokens()

    val material = darkColorScheme(
        primary = colors.ember,
        onPrimary = colors.emberInk,
        background = colors.bg,
        onBackground = colors.text,
        surface = colors.surface,
        onSurface = colors.text,
        error = colors.red,
    )

    // All-mono typography baseline; component-level sizing overrides as needed.
    val baseStyle = TextStyle(fontFamily = JetBrainsMono)
    val typography = Typography().run {
        copy(
            displayLarge = displayLarge.merge(baseStyle),
            displayMedium = displayMedium.merge(baseStyle),
            displaySmall = displaySmall.merge(baseStyle),
            headlineLarge = headlineLarge.merge(baseStyle),
            headlineMedium = headlineMedium.merge(baseStyle),
            headlineSmall = headlineSmall.merge(baseStyle),
            titleLarge = titleLarge.merge(baseStyle),
            titleMedium = titleMedium.merge(baseStyle),
            titleSmall = titleSmall.merge(baseStyle),
            bodyLarge = bodyLarge.merge(baseStyle),
            bodyMedium = bodyMedium.merge(baseStyle),
            bodySmall = bodySmall.merge(baseStyle),
            labelLarge = labelLarge.merge(baseStyle),
            labelMedium = labelMedium.merge(baseStyle),
            labelSmall = labelSmall.merge(baseStyle),
        )
    }

    androidx.compose.runtime.CompositionLocalProvider(
        LocalFire2MqttColors provides colors,
        LocalFocusTokens provides focus,
    ) {
        MaterialTheme(colorScheme = material, typography = typography, content = content)
    }
}
