"""Integration tests for Fire2MQTT button entities."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.conftest import TOPIC_CMD_LAUNCH, TOPIC_STATUS

NETFLIX_BUTTON = "button.fire_tv_test_device_launch_netflix"
JELLYFIN_BUTTON = "button.fire_tv_test_device_launch_jellyfin"


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_app_buttons_created(hass: HomeAssistant, setup_integration):
    assert hass.states.get(NETFLIX_BUTTON) is not None
    assert hass.states.get(JELLYFIN_BUTTON) is not None


async def test_netflix_button_press_publishes_package(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("button", "press", {"entity_id": NETFLIX_BUTTON}, blocking=True)
    assert (TOPIC_CMD_LAUNCH, "com.netflix.ninja") in mock_mqtt_publish.published


async def test_jellyfin_button_press_publishes_package(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("button", "press", {"entity_id": JELLYFIN_BUTTON}, blocking=True)
    assert (TOPIC_CMD_LAUNCH, "org.jellyfin.androidtv") in mock_mqtt_publish.published
