"""Integration tests for Fire2MQTT remote entity."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

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


async def test_remote_unavailable_when_offline(hass: HomeAssistant, setup_integration):
    assert hass.states.get(REMOTE).state == "unavailable"


async def test_remote_reflects_screen_state(hass: HomeAssistant, online, mock_mqtt_subscribe):
    import json

    from tests.conftest import TOPIC_SCREEN

    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": True, "ts": 1}))
    await hass.async_block_till_done()
    assert hass.states.get(REMOTE).state == "on"

    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": False, "ts": 2}))
    await hass.async_block_till_done()
    assert hass.states.get(REMOTE).state == "off"


async def test_remote_power_is_not_supported(hass: HomeAssistant, online, mock_mqtt_publish):
    from tests.conftest import TOPIC_CMD_POWER

    # Power can't be controlled from the stick — turn_on/off must raise, not silently no-op.
    for service in ("turn_on", "turn_off"):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call("remote", service, {"entity_id": REMOTE}, blocking=True)
    assert all(topic != TOPIC_CMD_POWER for topic, _ in mock_mqtt_publish.published)


async def test_send_command_num_repeats(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call(
        "remote", "send_command",
        {"entity_id": REMOTE, "command": ["DPAD_DOWN"], "num_repeats": 3, "delay_secs": 0},
        blocking=True,
    )
    sent = [p for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_KEY]
    assert sent == ["DPAD_DOWN", "DPAD_DOWN", "DPAD_DOWN"]
