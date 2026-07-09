"""Two Fire Sticks side by side: state and commands must stay isolated."""
from __future__ import annotations

import json
from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

PREFIX = "fire2mqtt"


async def _settle(hass: HomeAssistant) -> None:
    """Advance past the media_player state debounce so a pending transition commits."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()


def _entry(hass: HomeAssistant, device_id: str, title: str) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain="fire2mqtt",
        title=title,
        unique_id=f"fire2mqtt_{device_id}",
        data={"device_id": device_id, "topic_prefix": PREFIX},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def two_devices(hass: HomeAssistant, mock_mqtt_subscribe, mock_mqtt_publish):
    from homeassistant.config_entries import ConfigEntryState

    living = _entry(hass, "living_room", "Living Room Fire TV")
    bedroom = _entry(hass, "bedroom", "Bedroom Fire TV")
    # Setting up the first entry loads the component, which auto-sets-up the rest.
    for entry in (living, bedroom):
        if entry.state is ConfigEntryState.NOT_LOADED:
            await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield living, bedroom
    for entry in (living, bedroom):
        if entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_both_media_players_created(hass: HomeAssistant, two_devices):
    assert hass.states.get("media_player.living_room_fire_tv") is not None
    assert hass.states.get("media_player.bedroom_fire_tv") is not None


async def test_state_is_isolated_per_device(hass: HomeAssistant, two_devices, mock_mqtt_subscribe):
    await mock_mqtt_subscribe.deliver(f"{PREFIX}/living_room/status", "online")
    await hass.async_block_till_done()

    assert hass.states.get("media_player.living_room_fire_tv").state != "unavailable"
    assert hass.states.get("media_player.bedroom_fire_tv").state == "unavailable"

    await mock_mqtt_subscribe.deliver(f"{PREFIX}/bedroom/status", "online")
    await mock_mqtt_subscribe.deliver(
        f"{PREFIX}/bedroom/state/app",
        json.dumps({"package": "com.netflix.ninja", "name": "Netflix"}),
    )
    await mock_mqtt_subscribe.deliver(
        f"{PREFIX}/bedroom/state/playback",
        json.dumps({"media_session_state": 3, "title": "Show"}),
    )
    await hass.async_block_till_done()
    await _settle(hass)

    assert hass.states.get("media_player.bedroom_fire_tv").state == "playing"
    assert hass.states.get("media_player.living_room_fire_tv").state == "idle"


async def test_commands_target_the_right_device(hass: HomeAssistant, two_devices, mock_mqtt_subscribe, mock_mqtt_publish):
    await mock_mqtt_subscribe.deliver(f"{PREFIX}/living_room/status", "online")
    await mock_mqtt_subscribe.deliver(f"{PREFIX}/bedroom/status", "online")
    await hass.async_block_till_done()

    await hass.services.async_call(
        "media_player", "media_play",
        {"entity_id": "media_player.bedroom_fire_tv"},
        blocking=True,
    )
    assert (f"{PREFIX}/bedroom/cmd/media", "play") in mock_mqtt_publish.published
    assert all(t != f"{PREFIX}/living_room/cmd/media" for t, _ in mock_mqtt_publish.published)


async def test_devices_registered_separately(hass: HomeAssistant, two_devices, mock_mqtt_subscribe):
    from homeassistant.helpers import device_registry as dr

    # Both report the same model — names must stay distinct.
    for device_id in ("living_room", "bedroom"):
        await mock_mqtt_subscribe.deliver(
            f"{PREFIX}/{device_id}/state/device",
            json.dumps({"model": "Fire TV Stick 4K", "fire_os": "7.6.9.0", "schema_version": 1}),
        )
    await hass.async_block_till_done()

    registry = dr.async_get(hass)
    living = registry.async_get_device(identifiers={("fire2mqtt", "living_room")})
    bedroom = registry.async_get_device(identifiers={("fire2mqtt", "bedroom")})
    assert living is not None and bedroom is not None
    assert living.id != bedroom.id
    assert living.name == "Living Room Fire TV"
    assert bedroom.name == "Bedroom Fire TV"
    assert living.model == bedroom.model == "Fire TV Stick 4K"
