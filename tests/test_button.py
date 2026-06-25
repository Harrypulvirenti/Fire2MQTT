"""Integration tests for the Fire2MQTT Launch button."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.fire2mqtt.const import ADB_PORT
from tests.conftest import TOPIC_APPS, TOPIC_CMD_LAUNCH, TOPIC_DEVICE, TOPIC_STATUS

BUTTON = "button.fire_tv_test_device_launch_app"
REPROVISION = "button.fire_tv_test_device_re_provision_over_adb"
SELECT = "select.fire_tv_test_device_app_launcher"
INSTALLED = ["com.netflix.ninja", "org.jellyfin.androidtv"]


@pytest.fixture
async def online_with_apps(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_APPS, json.dumps({"packages": INSTALLED, "ts": 1}))
    await hass.async_block_till_done()


async def _select(hass: HomeAssistant, option: str) -> None:
    await hass.services.async_call(
        "select", "select_option", {"entity_id": SELECT, "option": option}, blocking=True
    )


async def test_launch_button_launches_the_selected_app(
    hass: HomeAssistant, online_with_apps, mock_mqtt_publish
):
    await _select(hass, "Netflix")
    await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)
    assert (TOPIC_CMD_LAUNCH, "com.netflix.ninja") in mock_mqtt_publish.published


async def test_launch_button_without_a_selection_raises(hass: HomeAssistant, online_with_apps):
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)


# ── Re-provision button ───────────────────────────────────────────────────────

async def test_reprovision_pushes_config_over_adb(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(
        TOPIC_DEVICE,
        json.dumps({"model": "Fire TV", "fire_os": "11", "ip": "10.0.0.88", "app_version": "0.4.1"}),
    )
    await hass.async_block_till_done()

    config = object()  # opaque; we only assert it's forwarded
    provision = AsyncMock()
    with (
        patch(
            "custom_components.fire2mqtt.adb_provision.async_recovery_broker_config",
            AsyncMock(return_value=config),
        ),
        patch("custom_components.fire2mqtt.adb_provision.async_provision", provision),
    ):
        await hass.services.async_call(
            "button", "press", {"entity_id": REPROVISION}, blocking=True
        )
    provision.assert_awaited_once_with(hass, "10.0.0.88", config, ADB_PORT)


async def test_reprovision_without_device_ip_raises(hass: HomeAssistant, online_with_apps):
    # No state/device delivered → no IP to target.
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button", "press", {"entity_id": REPROVISION}, blocking=True
        )


async def test_reprovision_without_mqtt_broker_raises(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(
        TOPIC_DEVICE, json.dumps({"model": "Fire TV", "fire_os": "11", "ip": "10.0.0.88"})
    )
    await hass.async_block_till_done()

    with patch(
        "custom_components.fire2mqtt.adb_provision.async_recovery_broker_config",
        AsyncMock(return_value=None),  # no MQTT broker configured
    ):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "button", "press", {"entity_id": REPROVISION}, blocking=True
            )
