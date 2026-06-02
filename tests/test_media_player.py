"""Integration tests for the Fire2MQTT media_player entity."""
from __future__ import annotations

import json

import pytest
from homeassistant.components.media_player import (
    ATTR_MEDIA_ARTIST,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_POSITION,
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
)
from homeassistant.core import HomeAssistant

from tests.conftest import (
    TOPIC_APP,
    TOPIC_CMD_LAUNCH,
    TOPIC_CMD_MEDIA,
    TOPIC_CMD_POWER,
    TOPIC_CMD_VOLUME,
    TOPIC_PLAYBACK,
    TOPIC_STATUS,
    TOPIC_VOLUME,
)

ENTITY_ID = "media_player.fire_tv_test_device"


@pytest.fixture
async def online(hass: HomeAssistant, setup_integration, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "online")
    await hass.async_block_till_done()


async def test_entity_created(hass: HomeAssistant, setup_integration):
    assert hass.states.get(ENTITY_ID) is not None


async def test_unavailable_when_offline(hass: HomeAssistant, setup_integration):
    assert hass.states.get(ENTITY_ID).state == "unavailable"


async def test_idle_when_online(hass: HomeAssistant, online, mock_mqtt_subscribe):
    assert hass.states.get(ENTITY_ID).state == "idle"


async def test_state_playing(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix"}))
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({"media_session_state": 3, "title": "Stranger Things", "artist": None, "album": None, "duration_ms": 3600000, "position_ms": 600000}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "playing"


async def test_state_paused(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix"}))
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({"media_session_state": 2, "title": "Stranger Things", "artist": None, "album": None, "duration_ms": 3600000, "position_ms": 600000}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "paused"


async def test_goes_back_offline(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_STATUS, "offline")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unavailable"


async def test_media_attributes(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({
        "media_session_state": 3,
        "title": "Demon Slayer",
        "artist": "Ufotable",
        "album": None,
        "duration_ms": 1440000,
        "position_ms": 300000,
    }))
    await hass.async_block_till_done()
    attrs = hass.states.get(ENTITY_ID).attributes
    assert attrs.get(ATTR_MEDIA_TITLE) == "Demon Slayer"
    assert attrs.get(ATTR_MEDIA_ARTIST) == "Ufotable"
    assert attrs.get(ATTR_MEDIA_DURATION) == 1440.0
    assert attrs.get(ATTR_MEDIA_POSITION) == 300.0


async def test_volume_level_normalised(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_VOLUME, json.dumps({"level": 6, "max": 15, "mute": False}))
    await hass.async_block_till_done()
    level = hass.states.get(ENTITY_ID).attributes.get(ATTR_MEDIA_VOLUME_LEVEL)
    assert abs(level - 6 / 15) < 0.01


async def test_volume_muted(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_VOLUME, json.dumps({"level": 6, "max": 15, "mute": True}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).attributes.get(ATTR_MEDIA_VOLUME_MUTED) is True


async def test_media_play_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "media_play", {"entity_id": ENTITY_ID}, blocking=True)
    assert (TOPIC_CMD_MEDIA, "play") in mock_mqtt_publish.published


async def test_media_pause_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "media_pause", {"entity_id": ENTITY_ID}, blocking=True)
    assert (TOPIC_CMD_MEDIA, "pause") in mock_mqtt_publish.published


async def test_media_stop_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "media_stop", {"entity_id": ENTITY_ID}, blocking=True)
    assert (TOPIC_CMD_MEDIA, "stop") in mock_mqtt_publish.published


async def test_next_track_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "media_next_track", {"entity_id": ENTITY_ID}, blocking=True)
    assert (TOPIC_CMD_MEDIA, "next") in mock_mqtt_publish.published


async def test_set_volume_publishes(hass: HomeAssistant, online, mock_mqtt_subscribe, mock_mqtt_publish):
    await mock_mqtt_subscribe.deliver(TOPIC_VOLUME, json.dumps({"level": 8, "max": 15, "mute": False}))
    await hass.async_block_till_done()
    await hass.services.async_call("media_player", "volume_set", {"entity_id": ENTITY_ID, "volume_level": 0.4}, blocking=True)
    volume_publishes = [json.loads(p) for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_VOLUME]
    assert any(p.get("action") == "set" and p.get("level") == round(0.4 * 15) for p in volume_publishes)


async def test_mute_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "volume_mute", {"entity_id": ENTITY_ID, "is_volume_muted": True}, blocking=True)
    volume_publishes = [json.loads(p) for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_VOLUME]
    assert any(p.get("action") == "mute" for p in volume_publishes)


async def test_unmute_publishes(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "volume_mute", {"entity_id": ENTITY_ID, "is_volume_muted": False}, blocking=True)
    volume_publishes = [json.loads(p) for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_VOLUME]
    assert any(p.get("action") == "unmute" for p in volume_publishes)


async def test_turn_off_publishes_sleep(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "turn_off", {"entity_id": ENTITY_ID}, blocking=True)
    assert any(t == TOPIC_CMD_POWER and p == "sleep" for t, p in mock_mqtt_publish.published)


async def test_select_source_publishes_launch(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "select_source", {"entity_id": ENTITY_ID, "source": "Netflix"}, blocking=True)
    assert any(t == TOPIC_CMD_LAUNCH and p == "com.netflix.ninja" for t, p in mock_mqtt_publish.published)
