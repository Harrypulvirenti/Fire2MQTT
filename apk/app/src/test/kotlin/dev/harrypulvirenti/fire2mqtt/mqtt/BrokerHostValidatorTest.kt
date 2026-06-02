package dev.harrypulvirenti.fire2mqtt.mqtt

import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.ValueSource

class BrokerHostValidatorTest {

    @ParameterizedTest
    @ValueSource(strings = ["", "   ", "\t"])
    fun `blank host returns null`(host: String) {
        assertNull(BrokerHostValidator.resolveToPrivateAddress(host))
    }

    @Test fun `loopback address is valid`() {
        assertNotNull(BrokerHostValidator.resolveToPrivateAddress("127.0.0.1"))
    }

    @ParameterizedTest
    @ValueSource(strings = ["192.168.1.1", "10.0.0.1", "10.10.10.10", "172.16.0.1", "172.31.255.255"])
    fun `RFC1918 private addresses are valid`(host: String) {
        assertNotNull(BrokerHostValidator.resolveToPrivateAddress(host))
    }

    @ParameterizedTest
    @ValueSource(strings = ["8.8.8.8", "1.1.1.1", "93.184.216.34"])
    fun `public IP addresses are rejected`(host: String) {
        assertNull(BrokerHostValidator.resolveToPrivateAddress(host))
    }

    @Test fun `unresolvable hostname returns null`() {
        assertNull(BrokerHostValidator.resolveToPrivateAddress("host.invalid"))
    }
}
