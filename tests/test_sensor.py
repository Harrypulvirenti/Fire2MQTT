"""Integration tests for Fire2MQTT sensor entities."""
from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.conftest import TOPIC_APP, TOPIC_PLAYBACK, TOPIC_STATUS, TOPIC_VOLUME

CURRENT_APP = "sensor.fire_tv_test_device_current_app"
CURRENT_APP_PKG = "sensor.fire_tv_test_device_current_app_package"
MEDIA_TITLE = "sensor.fire_tv_test_device_media_title"
MEDIA_ARTIST = "sensor.fire_tv_test_device_media_artist"
VOLUME_LEVEL = "sensor.fire_tv_test_device_volume_level"


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_all_sensors_created(hass: HomeAssistant, setup_integration):
    registry = er.async_get(hass)
    # Enabled sensors appear in hass.states; disabled-by-default sensors only in the registry.
    for entity_id in (CURRENT_APP, MEDIA_TITLE, MEDIA_ARTIST, VOLUME_LEVEL):
        assert hass.states.get(entity_id) is not None, f"missing {entity_id}"
    assert registry.async_get(CURRENT_APP_PKG) is not None, f"missing {CURRENT_APP_PKG} in registry"


async def test_current_app_updates(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix"}))
    await hass.async_block_till_done()
    state = hass.states.get(CURRENT_APP)
    assert state.state == "Netflix"
    assert state.attributes.get("package") == "com.netflix.ninja"


async def test_current_app_package_sensor(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    # Entity is disabled-by-default — verify it exists in the registry with the correct value
    # by checking the entity entry and reading from the coordinator directly.
    registry = er.async_get(hass)
    entry = registry.async_get(CURRENT_APP_PKG)
    assert entry is not None
    assert entry.disabled_by is not None  # disabled by integration intent

    # Deliver app data and confirm the coordinator holds the right package name
    # (the entity reads from coordinator.data.app["package"]).
    await mock_mqtt_subscribe.deliver(TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix"}))
    await hass.async_block_till_done()
    from custom_components.fire2mqtt.coordinator import Fire2MqttCoordinator
    coordinator: Fire2MqttCoordinator = setup_integration.runtime_data.coordinator
    assert coordinator.data.app.get("package") == "com.netflix.ninja"


async def test_media_title_sensor(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({
        "media_session_state": 3, "title": "Demon Slayer S4E01",
        "artist": None, "album": None, "duration_ms": None, "position_ms": None,
    }))
    await hass.async_block_till_done()
    assert hass.states.get(MEDIA_TITLE).state == "Demon Slayer S4E01"


async def test_media_artist_sensor(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({
        "media_session_state": 3, "title": "Song", "artist": "Ufotable",
        "album": None, "duration_ms": None, "position_ms": None,
    }))
    await hass.async_block_till_done()
    assert hass.states.get(MEDIA_ARTIST).state == "Ufotable"


async def test_volume_level_sensor_percentage(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_VOLUME, json.dumps({"level": 9, "max": 15, "mute": False}))
    await hass.async_block_till_done()
    state = hass.states.get(VOLUME_LEVEL)
    assert state.state == "60"  # round(9/15*100)
    assert state.attributes.get("raw_level") == 9
    assert state.attributes.get("max_level") == 15
    assert state.attributes.get("muted") is False


async def test_sensors_unavailable_when_offline(hass: HomeAssistant, setup_integration):
    for entity_id in (CURRENT_APP, MEDIA_TITLE, VOLUME_LEVEL):
        assert hass.states.get(entity_id).state == "unavailable"
