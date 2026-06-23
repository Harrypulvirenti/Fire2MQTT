package dev.harrypulvirenti.fire2mqtt.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import dev.harrypulvirenti.fire2mqtt.R

/**
 * JetBrains Mono — used throughout the UI (the design is all-mono). Static
 * weights are bundled in res/font so no network font provider is needed on
 * Fire OS.
 */
val JetBrainsMono = FontFamily(
    Font(R.font.jetbrains_mono_regular, FontWeight.Normal),
    Font(R.font.jetbrains_mono_medium, FontWeight.Medium),
    Font(R.font.jetbrains_mono_semibold, FontWeight.SemiBold),
    Font(R.font.jetbrains_mono_bold, FontWeight.Bold),
    Font(R.font.jetbrains_mono_extrabold, FontWeight.ExtraBold),
)

private fun mono(
    size: Int,
    weight: FontWeight = FontWeight.Normal,
    letterSpacing: Float = 0f,
) = TextStyle(
    fontFamily = JetBrainsMono,
    fontSize = size.sp,
    fontWeight = weight,
    letterSpacing = letterSpacing.sp,
)

/**
 * Typography tokens for the design system. Components reference these via
 * `Fire2MqttTheme.type` (colors stay per-call-site — the same style renders in
 * several colors). Sizes are design-canvas units (see TvDesignScale).
 */
@Immutable
object Fire2MqttType {
    /** "Fire2MQTT" wordmark in the header. */
    val wordmark = mono(30, FontWeight.Bold)
    /** Uppercased tagline under the wordmark. */
    val tagline = mono(13, FontWeight.Medium, letterSpacing = 3f)
    /** Uppercased card section titles (next to the ember pip). */
    val eyebrow = mono(15, FontWeight.SemiBold, letterSpacing = 3f)
    /** Pill badges (global status, ADB card title). */
    val badge = mono(17, FontWeight.SemiBold, letterSpacing = 2f)
    /** Big connection-state word in the status panel. */
    val statusTitle = mono(32, FontWeight.Bold)
    /** Row titles: field labels, permission names. */
    val label = mono(19, FontWeight.SemiBold)
    /** Compact (2-up) field labels. */
    val labelSmall = mono(18, FontWeight.SemiBold)
    /** Field input text / placeholders. */
    val value = mono(20, FontWeight.Medium)
    /** Compact field input text / placeholders. */
    val valueSmall = mono(19, FontWeight.Medium)
    /** The big port number in the stepper. */
    val stepperValue = mono(26, FontWeight.SemiBold)
    /** Uppercased micro-hints under field labels. */
    val hint = mono(12, letterSpacing = 1.5f)
    /** Uppercased captions (topic prefix label, hint-bar footer). */
    val caption = mono(13, letterSpacing = 1.5f)
    /** Plain body copy (helper text, ADB instructions, hint bar). */
    val body = mono(15).copy(lineHeight = 21.sp)
    /** Secondary descriptions inside rows. */
    val bodySmall = mono(14)
    /** In-card content text (status message, topic segments, perm state). */
    val itemBody = mono(18)
    /** Emphasised in-card content (topic highlights, ENABLED chip). */
    val itemEmphasis = mono(18, FontWeight.SemiBold)
    /** Secondary button label. */
    val button = mono(22, FontWeight.SemiBold)
    /** Primary CTA label. */
    val buttonPrimary = mono(23, FontWeight.Bold)
}
