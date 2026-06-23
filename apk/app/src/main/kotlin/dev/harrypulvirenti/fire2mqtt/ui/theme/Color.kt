package dev.harrypulvirenti.fire2mqtt.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Fire2MQTT design tokens — ember on warm near-black, ported 1:1 from the
 * Claude Design handoff (`index.html` :root). All Compose UI reads colors from
 * here (exposed via [Fire2MqttColors] / LocalFire2MqttColors), not from Material.
 */
object Fire2MqttPalette {
    // surfaces / elevation ramp
    val BgLetter = Color(0xFF050403)
    val Bg = Color(0xFF0B0908)
    val Surface = Color(0xFF16120E)
    val Surface2 = Color(0xFF1D1711)
    val Surface3 = Color(0xFF271F17)

    // hairlines
    val Line = Color(0x14FFEEE0)   // rgba(255,238,224,.08)
    val Line2 = Color(0x29FFEEE0)  // rgba(255,238,224,.16)

    // text ramp
    val Text = Color(0xFFF6EFE6)
    val Text2 = Color(0xFFB4AA9E)
    val Text3 = Color(0xFF7B7163)
    val Text4 = Color(0xFF564E44)

    // accents
    val Ember = Color(0xFFFF7A18)
    val Ember2 = Color(0xFFFFA24D)
    val EmberInk = Color(0xFF190B02)
    val Green = Color(0xFF5AD18C)
    val Amber = Color(0xFFFFB547)
    val Red = Color(0xFFFF6F60)
}
