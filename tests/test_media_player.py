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
    MediaPlayerEntityFeature,
)
from homeassistant.core import HomeAssistant

from tests.conftest import (
    TOPIC_APP,
    TOPIC_APPS,
    TOPIC_CMD_LAUNCH,
    TOPIC_CMD_MEDIA,
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


async def test_title_placeholder_when_playing_without_metadata(
    hass: HomeAssistant, online, mock_mqtt_subscribe
):
    """Prime Video (com.amazon.firebat) reports a playing state but no MediaSession
    metadata. The alias resolves it to the curated rules (→ playing) and the title
    line falls back to an explanatory placeholder instead of a blank/'Unknown'."""
    await mock_mqtt_subscribe.deliver(
        TOPIC_APP, json.dumps({"package": "com.amazon.firebat", "name": "Prime Video"})
    )
    await mock_mqtt_subscribe.deliver(
        TOPIC_PLAYBACK, json.dumps({"media_session_state": 3, "title": None})
    )
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state.state == "playing"
    assert state.attributes.get(ATTR_MEDIA_TITLE) == "Prime Video — no title info"


async def test_no_title_placeholder_when_idle(
    hass: HomeAssistant, online, mock_mqtt_subscribe
):
    """When nothing is playing, the title stays empty rather than showing a placeholder."""
    await mock_mqtt_subscribe.deliver(
        TOPIC_APP, json.dumps({"package": "com.amazon.firebat", "name": "Prime Video"})
    )
    await mock_mqtt_subscribe.deliver(
        TOPIC_PLAYBACK, json.dumps({"media_session_state": 0, "title": None})
    )
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state.state == "idle"
    assert state.attributes.get(ATTR_MEDIA_TITLE) is None


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


async def test_source_list_lists_only_installed_apps(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(
        TOPIC_APPS, json.dumps({"packages": ["com.netflix.ninja", "org.jellyfin.androidtv"], "ts": 1})
    )
    await hass.async_block_till_done()
    source_list = hass.states.get(ENTITY_ID).attributes["source_list"]
    assert source_list == ["Jellyfin", "Netflix"]
    assert "Plex" not in source_list


async def test_select_source_publishes_launch(hass: HomeAssistant, online, mock_mqtt_subscribe, mock_mqtt_publish):
    await mock_mqtt_subscribe.deliver(TOPIC_APPS, json.dumps({"packages": ["com.netflix.ninja"], "ts": 1}))
    await hass.async_block_till_done()
    await hass.services.async_call("media_player", "select_source", {"entity_id": ENTITY_ID, "source": "Netflix"}, blocking=True)
    assert any(t == TOPIC_CMD_LAUNCH and p == "com.netflix.ninja" for t, p in mock_mqtt_publish.published)


async def test_aliased_foreground_package_resolves_to_playing(
    hass: HomeAssistant, online, mock_mqtt_subscribe, monkeypatch
):
    """A foreground package known only as an alias still resolves to its curated
    rules (covers the Crunchyroll 'no playback while watching' case)."""
    from custom_components.fire2mqtt.data import apps as apps_mod

    alias = "com.netflix.ninja.firetv"
    monkeypatch.setitem(apps_mod.PACKAGE_TO_KEY, alias, "netflix")

    await mock_mqtt_subscribe.deliver(TOPIC_APP, json.dumps({"package": alias, "name": "Netflix"}))
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({"media_session_state": 3}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "playing"


async def test_no_power_buttons_exposed(hass: HomeAssistant, online):
    # The media_player must not advertise TURN_ON/TURN_OFF — the stick can't power the TV.
    feats = hass.states.get(ENTITY_ID).attributes["supported_features"]
    assert not (feats & MediaPlayerEntityFeature.TURN_ON)
    assert not (feats & MediaPlayerEntityFeature.TURN_OFF)


async def test_volume_up_publishes_step(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "volume_up", {"entity_id": ENTITY_ID}, blocking=True)
    volume_publishes = [json.loads(p) for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_VOLUME]
    assert any(p == {"action": "up"} for p in volume_publishes)


async def test_volume_down_publishes_step(hass: HomeAssistant, online, mock_mqtt_publish):
    await hass.services.async_call("media_player", "volume_down", {"entity_id": ENTITY_ID}, blocking=True)
    volume_publishes = [json.loads(p) for t, p in mock_mqtt_publish.published if t == TOPIC_CMD_VOLUME]
    assert any(p == {"action": "down"} for p in volume_publishes)


async def test_screen_off_reports_off(hass: HomeAssistant, online, mock_mqtt_subscribe):
    from tests.conftest import TOPIC_SCREEN

    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": False, "ts": 1}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "off"

    await mock_mqtt_subscribe.deliver(TOPIC_SCREEN, json.dumps({"on": True, "ts": 2}))
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state != "off"


async def test_media_position_updated_at_from_ts(hass: HomeAssistant, online, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(TOPIC_PLAYBACK, json.dumps({
        "media_session_state": 3, "title": "T", "position_ms": 1000,
        "duration_ms": 2000, "ts": 1747000000000,
    }))
    await hass.async_block_till_done()
    attrs = hass.states.get(ENTITY_ID).attributes
    updated_at = attrs.get("media_position_updated_at")
    assert updated_at is not None
    assert updated_at.timestamp() == 1747000000.0


async def test_launcher_reports_idle_then_standby(
    hass: HomeAssistant, online, mock_mqtt_subscribe, freezer
):
    from datetime import timedelta

    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    await mock_mqtt_subscribe.deliver(
        TOPIC_APP, json.dumps({"package": "com.amazon.tv.launcher", "name": "Home"})
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "idle"

    # Default idle timeout is 10 minutes; jump past it.
    freezer.tick(timedelta(minutes=11))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "standby"

    # Leaving the launcher resets standby detection.
    await mock_mqtt_subscribe.deliver(
        TOPIC_APP, json.dumps({"package": "com.netflix.ninja", "name": "Netflix"})
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "idle"
