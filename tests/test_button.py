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


async def test_stale_buttons_removed_when_app_disabled(hass: HomeAssistant, mock_mqtt_subscribe, mock_mqtt_publish):
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="fire2mqtt",
        title="Fire TV test_device",
        data={"device_id": "test_device", "topic_prefix": "fire2mqtt"},
        options={"enabled_apps": ["jellyfin"]},
    )
    entry.add_to_hass(hass)

    # Simulate a button left over from when netflix was enabled.
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "button", "fire2mqtt", "fire2mqtt_test_device_launch_netflix",
        config_entry=entry,
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert registry.async_get_entity_id("button", "fire2mqtt", "fire2mqtt_test_device_launch_netflix") is None
    assert registry.async_get_entity_id("button", "fire2mqtt", "fire2mqtt_test_device_launch_jellyfin") is not None

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
