package dev.harrypulvirenti.fire2mqtt.mqtt

import java.net.Inet4Address
import java.net.InetAddress

/**
 * Gate that ensures cleartext MQTT only goes to a private/LAN destination,
 * by pinning the MQTT client to an explicitly validated IP address.
 *
 * Why pin instead of "validate once and hand HiveMQ the hostname":
 *   - getByName() only inspects a single A/AAAA record, but a hostname can
 *     resolve to several addresses with non-deterministic order.
 *   - HiveMQ's auto-reconnect re-resolves the hostname on each reconnect,
 *     so even a once-validated hostname could later resolve to a public IP
 *     (DNS rebinding, record drift, mixed-result resolvers).
 *   - With process-wide cleartext enabled by network_security_config, this
 *     validator is the only enforcement point.
 *
 * Strategy: resolve every candidate via getAllByName, refuse if any is
 * public, then return a single chosen private IP as a string. The caller
 * passes that string to HiveMQ's serverHost(...), which then connects by
 * IP literal and never performs further DNS lookups.
 *
 * mDNS caveat: Android's Java DNS stub only resolves `.local` names via
 * mDNS on Android 12+. Fire OS 8 is based on Android 11, so `.local`
 * hostnames typically throw UnknownHostException here and are rejected —
 * users on those devices should configure the broker by an RFC1918 IP.
 */
object BrokerHostValidator {
    /**
     * @return the pinned IP literal to hand to HiveMQ's serverHost(...),
     *   or null if the host was blank, failed to resolve, resolved to no
     *   addresses, or had any public candidate among its answers.
     */
    fun resolveToPrivateAddress(host: String): String? {
        if (host.isBlank()) return null
        return try {
            val addresses = InetAddress.getAllByName(host)
            if (addresses.isEmpty()) return null
            if (addresses.any { !it.isPrivateOrLocal() }) return null
            val chosen = addresses.firstOrNull { it is Inet4Address && it.isSiteLocalAddress }
                ?: addresses.firstOrNull { it is Inet4Address }
                ?: addresses.first()
            chosen.hostAddress
        } catch (_: Exception) {
            null
        }
    }

    private fun InetAddress.isPrivateOrLocal(): Boolean =
        isLoopbackAddress || isSiteLocalAddress || isLinkLocalAddress || isAnyLocalAddress
}
