"""Integration tests for the Fire2MQTT Launch button."""
from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.conftest import TOPIC_APPS, TOPIC_CMD_LAUNCH, TOPIC_STATUS

BUTTON = "button.fire_tv_test_device_launch_app"
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
