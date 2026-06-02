"""Integration tests for Fire2MQTT remote entity."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.conftest import TOPIC_CMD_KEY, TOPIC_STATUS

REMOTE = "remote.fire_tv_test_device_remote"


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_remote_entity_created(hass: HomeAssistant, setup_integration):
    assert hass.states.get(REMOTE) is not None


async def test_send_home_key(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call(
        "remote", "send_command",
        {"entity_id": REMOTE, "command": ["HOME"]},
        blocking=True,
    )
    assert (TOPIC_CMD_KEY, "HOME") in mock_mqtt_publish.published


async def test_send_multiple_keys(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call(
        "remote", "send_command",
        {"entity_id": REMOTE, "command": ["DPAD_UP", "DPAD_CENTER"]},
        blocking=True,
    )
    assert (TOPIC_CMD_KEY, "DPAD_UP") in mock_mqtt_publish.published
    assert (TOPIC_CMD_KEY, "DPAD_CENTER") in mock_mqtt_publish.published


async def test_command_is_uppercased(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call(
        "remote", "send_command",
        {"entity_id": REMOTE, "command": ["home"]},
        blocking=True,
    )
    assert (TOPIC_CMD_KEY, "HOME") in mock_mqtt_publish.published
