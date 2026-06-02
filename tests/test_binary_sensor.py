"""Integration tests for Fire2MQTT binary_sensor entities."""
from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant

from tests.conftest import TOPIC_SCREEN, TOPIC_STATUS

SCREEN = "binary_sensor.fire_tv_test_device_screen"


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_screen_entity_created(hass: HomeAssistant, setup_integration):
    assert hass.states.get(SCREEN) is not None


async def test_screen_unavailable_when_offline(hass: HomeAssistant, setup_integration):
    assert hass.states.get(SCREEN).state == "unavailable"


async def test_screen_on(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": True, "ts": 1747000000000}))
    await hass.async_block_till_done()
    assert hass.states.get(SCREEN).state == "on"


async def test_screen_off(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": False, "ts": 1747000000000}))
    await hass.async_block_till_done()
    assert hass.states.get(SCREEN).state == "off"
