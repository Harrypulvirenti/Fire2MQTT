"""Tests for the device registry entry created by Fire2MQTT entities."""
from __future__ import annotations

import json

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from tests.conftest import DEVICE_ID, TOPIC_DEVICE, TOPIC_STATUS


async def test_device_named_after_entry_title_not_model(
    hass: HomeAssistant, setup_integration, mock_mqtt_subscribe
):
    """Two sticks of the same model must keep their user-chosen names."""
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, json.dumps({
        "model": "Fire TV Stick 4K",
        "fire_os": "7.6.9.0",
        "ip": "192.168.1.50",
        "mac": "AA:BB:CC:DD:EE:FF",
        "schema_version": 1,
    }))
    await hass.async_block_till_done()

    registry = dr.async_get(hass)
    device = registry.async_get_device(identifiers={("fire2mqtt", DEVICE_ID)})
    assert device is not None
    assert device.name == f"Fire TV {DEVICE_ID}"  # the config entry title
    assert device.model == "Fire TV Stick 4K"
    assert device.sw_version == "7.6.9.0"
    assert (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in device.connections
