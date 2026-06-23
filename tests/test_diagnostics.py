"""Tests for Fire2MQTT diagnostics."""
from __future__ import annotations

import json

from homeassistant.core import HomeAssistant

from custom_components.fire2mqtt.diagnostics import async_get_config_entry_diagnostics
from tests.conftest import TOPIC_DEVICE, TOPIC_STATUS


async def test_diagnostics_redacts_network_identifiers(
    hass: HomeAssistant, setup_integration, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, json.dumps({
        "model": "Fire TV Stick 4K",
        "fire_os": "7.6.9.0",
        "ip": "192.168.1.50",
        "mac": "AA:BB:CC:DD:EE:FF",
        "schema_version": 1,
    }))
    await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, setup_integration)

    assert diag["state"]["online"] is True
    assert diag["state"]["device"]["model"] == "Fire TV Stick 4K"
    assert diag["state"]["device"]["ip"] == "**REDACTED**"
    assert diag["state"]["device"]["mac"] == "**REDACTED**"
    assert diag["entry"]["data"]["device_id"] == "test_device"
