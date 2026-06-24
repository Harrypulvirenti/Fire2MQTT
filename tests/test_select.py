"""Integration tests for the Fire2MQTT app-launcher select entity."""
from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.conftest import (
    DEVICE_ID,
    PREFIX,
    TOPIC_APP,
    TOPIC_APPS,
    TOPIC_CMD_LAUNCH,
    TOPIC_STATUS,
)

SELECT = "select.fire_tv_test_device_app_launcher"

# Netflix, Prime Video, Jellyfin installed; Plex/Kodi deliberately absent.
INSTALLED = [
    "com.netflix.ninja",
    "com.amazon.avod.thirdpartyclient",
    "org.jellyfin.androidtv",
]


@pytest.fixture
async def online_with_apps(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_APPS, json.dumps({"packages": INSTALLED, "ts": 1}))
    await hass.async_block_till_done()


async def test_options_are_installed_curated_apps(hass: HomeAssistant, online_with_apps):
    state = hass.states.get(SELECT)
    assert state is not None
    assert state.attributes["options"] == ["Jellyfin", "Netflix", "Prime Video"]
    # Curated-but-not-installed apps never appear.
    assert "Plex" not in state.attributes["options"]
    assert "Kodi" not in state.attributes["options"]


async def test_options_empty_before_inventory(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()
    assert hass.states.get(SELECT).attributes["options"] == []


async def test_select_option_launches_matched_package(
    hass: HomeAssistant, online_with_apps, mock_mqtt_publish
):
    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": SELECT, "option": "Netflix"}, blocking=True,
    )
    assert (TOPIC_CMD_LAUNCH, "com.netflix.ninja") in mock_mqtt_publish.published


async def test_current_option_reflects_foreground_app(
    hass: HomeAssistant, online_with_apps, mock_mqtt_subscribe
):
    await mock_mqtt_subscribe.deliver(
        TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix", "ts": 2})
    )
    await hass.async_block_till_done()
    assert hass.states.get(SELECT).state == "Netflix"


async def test_enabled_apps_option_narrows_choices(
    hass: HomeAssistant, mock_mqtt_subscribe, mock_mqtt_publish
):
    entry = MockConfigEntry(
        domain="fire2mqtt",
        title=f"Fire TV {DEVICE_ID}",
        data={"device_id": DEVICE_ID, "topic_prefix": PREFIX},
        options={"enabled_apps": ["jellyfin"]},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await mock_mqtt_subscribe.deliver(TOPIC_APPS, json.dumps({"packages": INSTALLED, "ts": 1}))
    await hass.async_block_till_done()

    # Netflix/Prime are installed but not enabled → only Jellyfin shows.
    assert hass.states.get(SELECT).attributes["options"] == ["Jellyfin"]

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_legacy_launch_buttons_purged_on_setup(
    hass: HomeAssistant, mock_mqtt_subscribe, mock_mqtt_publish
):
    from homeassistant.helpers import entity_registry as er

    entry = MockConfigEntry(
        domain="fire2mqtt",
        title=f"Fire TV {DEVICE_ID}",
        data={"device_id": DEVICE_ID, "topic_prefix": PREFIX},
        options={},
    )
    entry.add_to_hass(hass)

    registry = er.async_get(hass)
    registry.async_get_or_create(
        "button", "fire2mqtt", "fire2mqtt_test_device_launch_netflix", config_entry=entry,
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert registry.async_get_entity_id(
        "button", "fire2mqtt", "fire2mqtt_test_device_launch_netflix"
    ) is None

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
