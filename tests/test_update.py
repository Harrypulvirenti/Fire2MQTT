"""Integration tests for the Fire2MQTT APK update entity."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fire2mqtt.const import ADB_PORT
from tests.conftest import TOPIC_DEVICE, TOPIC_STATUS

UPDATE = "update.fire_tv_test_device_app"

# Matches custom_components/fire2mqtt/manifest.json (lockstep with the APK).
CURRENT_VERSION = "0.2.0-beta5"


def _device(app_version: str | None, ip: str = "10.0.0.50") -> str:
    payload: dict = {"model": "Fire TV", "fire_os": "8", "ip": ip, "mac": "aa:bb:cc:dd:ee:ff"}
    if app_version is not None:
        payload["app_version"] = app_version
    return json.dumps(payload)


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_unknown_until_device_reports_version(hass: HomeAssistant, online):
    # No state/device yet → installed version unknown.
    assert hass.states.get(UPDATE).state == "unknown"


async def test_update_available_for_old_apk(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, _device("0.1.0"))
    await hass.async_block_till_done()
    state = hass.states.get(UPDATE)
    assert state.state == "on"  # update available
    assert state.attributes["installed_version"] == "0.1.0"
    assert state.attributes["latest_version"] == CURRENT_VERSION


async def test_up_to_date_when_versions_match(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, _device(CURRENT_VERSION))
    await hass.async_block_till_done()
    assert hass.states.get(UPDATE).state == "off"  # up to date


async def test_install_pushes_apk_over_adb_with_device_ip(
    hass: HomeAssistant, online, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, _device("0.1.0", ip="10.0.0.77"))
    await hass.async_block_till_done()

    mock = AsyncMock()
    with patch("custom_components.fire2mqtt.adb_provision.async_update_apk", mock):
        await hass.services.async_call(
            "update", "install", {"entity_id": UPDATE}, blocking=True
        )
    mock.assert_awaited_once_with(hass, "10.0.0.77", ADB_PORT)


async def test_install_raises_when_ip_unknown(hass: HomeAssistant, online, mock_mqtt_subscribe):
    from homeassistant.exceptions import HomeAssistantError

    # Device reports a version but no IP → install can't pick an ADB host.
    await mock_mqtt_subscribe.deliver(TOPIC_DEVICE, _device("0.1.0", ip=""))
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "update", "install", {"entity_id": UPDATE}, blocking=True
        )
