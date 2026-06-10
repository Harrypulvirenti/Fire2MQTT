"""Tests for the Fire2MQTT coordinator."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fire2mqtt.const import (
    TOPIC_CMD_KEY,
    TOPIC_CMD_LAUNCH,
    TOPIC_CMD_MEDIA,
    TOPIC_CMD_POWER,
    TOPIC_CMD_VOLUME,
    TOPIC_STATE_APP,
    TOPIC_STATE_DEVICE,
    TOPIC_STATE_PLAYBACK,
    TOPIC_STATE_SCREEN,
    TOPIC_STATE_VOLUME,
    TOPIC_STATUS,
)
from custom_components.fire2mqtt.coordinator import Fire2MqttCoordinator


@pytest.fixture
def coordinator(hass):
    entry = MockConfigEntry(
        domain="fire2mqtt",
        title="Fire TV test_device",
        data={"device_id": "test_device", "topic_prefix": "fire2mqtt"},
    )
    entry.add_to_hass(hass)
    return Fire2MqttCoordinator(hass, entry, topic_prefix="fire2mqtt", device_id="test_device")


def make_msg(payload: str | dict) -> MagicMock:
    msg = MagicMock()
    msg.payload = payload if isinstance(payload, str) else json.dumps(payload)
    return msg


def test_status_online_updates_coordinator(coordinator):
    coordinator._on_status(make_msg("online"))
    assert coordinator.data.online is True


def test_status_offline_updates_coordinator(coordinator):
    coordinator.data.online = True
    coordinator._on_status(make_msg("offline"))
    assert coordinator.data.online is False


def test_playback_callback_updates_data(coordinator):
    payload = {"media_session_state": 3, "title": "Test Show", "app": "com.netflix.ninja"}
    coordinator._on_playback(make_msg(payload))
    assert coordinator.data.playback["media_session_state"] == 3
    assert coordinator.data.playback["title"] == "Test Show"


def test_app_callback_updates_data(coordinator):
    payload = {"package": "com.netflix.ninja", "name": "Netflix", "ts": 123}
    coordinator._on_app(make_msg(payload))
    assert coordinator.data.app["package"] == "com.netflix.ninja"


def test_screen_callback_updates_data(coordinator):
    coordinator._on_screen(make_msg({"on": True, "ts": 123}))
    assert coordinator.data.screen["on"] is True


def test_volume_callback_updates_data(coordinator):
    coordinator._on_volume(make_msg({"level": 8, "max": 15, "mute": False, "ts": 123}))
    assert coordinator.data.volume["level"] == 8


def test_invalid_json_does_not_crash(coordinator):
    coordinator._on_playback(make_msg("not-json"))
    assert coordinator.data.playback == {}


def test_topic_builder(coordinator):
    assert coordinator._bus.topic("{prefix}/{device_id}/status") == "fire2mqtt/test_device/status"


def test_non_object_json_is_rejected(coordinator):
    coordinator._on_playback(make_msg('"just a string"'))
    coordinator._on_playback(make_msg("42"))
    assert coordinator.data.playback == {}


def test_device_info_callback_updates_data(coordinator):
    coordinator._on_device_info(make_msg({"model": "Fire TV Stick 4K", "fire_os": "7.6.9.0"}))
    assert coordinator.data.device_info["model"] == "Fire TV Stick 4K"
    assert coordinator.data.device_info["fire_os"] == "7.6.9.0"


# ── command publishing ────────────────────────────────────────────────────────

@pytest.fixture
def mock_publish():
    published: list[tuple] = []

    async def _publish(hass, topic, payload, **kwargs):
        published.append((topic, payload))

    mock = AsyncMock(side_effect=_publish)
    mock.published = published
    return mock


async def test_async_launch_app_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_launch_app("com.netflix.ninja")
    topic = TOPIC_CMD_LAUNCH.format(prefix="fire2mqtt", device_id="test_device")
    assert (topic, "com.netflix.ninja") in mock_publish.published


async def test_async_send_key_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_send_key("KEYCODE_HOME")
    topic = TOPIC_CMD_KEY.format(prefix="fire2mqtt", device_id="test_device")
    assert (topic, "KEYCODE_HOME") in mock_publish.published


async def test_async_media_command_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_media_command("play")
    topic = TOPIC_CMD_MEDIA.format(prefix="fire2mqtt", device_id="test_device")
    assert (topic, "play") in mock_publish.published


async def test_async_set_volume_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_set_volume(10)
    topic = TOPIC_CMD_VOLUME.format(prefix="fire2mqtt", device_id="test_device")
    payloads = [json.loads(p) for t, p in mock_publish.published if t == topic]
    assert any(p == {"action": "set", "level": 10} for p in payloads)


async def test_async_mute_volume_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_mute_volume(True)
    topic = TOPIC_CMD_VOLUME.format(prefix="fire2mqtt", device_id="test_device")
    payloads = [json.loads(p) for t, p in mock_publish.published if t == topic]
    assert any(p == {"action": "mute"} for p in payloads)


async def test_async_unmute_volume_publishes(hass, coordinator, mock_publish):
    with patch("homeassistant.components.mqtt.async_publish", mock_publish):
        await coordinator.async_mute_volume(False)
    topic = TOPIC_CMD_VOLUME.format(prefix="fire2mqtt", device_id="test_device")
    payloads = [json.loads(p) for t, p in mock_publish.published if t == topic]
    assert any(p == {"action": "unmute"} for p in payloads)


# ── subscription lifecycle ────────────────────────────────────────────────────

async def test_async_setup_subscribes_all_topics(hass, coordinator):
    subscribed_topics: list[str] = []
    unsub = MagicMock()

    async def _subscribe(h, topic, cb):
        subscribed_topics.append(topic)
        return unsub

    with patch("homeassistant.components.mqtt.async_subscribe", side_effect=_subscribe):
        await coordinator.async_setup()

    expected = {
        TOPIC_STATUS, TOPIC_STATE_PLAYBACK, TOPIC_STATE_APP,
        TOPIC_STATE_SCREEN, TOPIC_STATE_VOLUME, TOPIC_STATE_DEVICE,
    }
    actual = {t.format(prefix="fire2mqtt", device_id="test_device") for t in expected}
    assert set(subscribed_topics) == actual


async def test_async_teardown_calls_all_unsubs(hass, coordinator):
    unsubs = [MagicMock() for _ in range(6)]
    call_iter = iter(unsubs)

    async def _subscribe(h, topic, cb):
        return next(call_iter)

    with patch("homeassistant.components.mqtt.async_subscribe", side_effect=_subscribe):
        await coordinator.async_setup()

    await coordinator.async_teardown()

    for unsub in unsubs:
        unsub.assert_called_once()
    assert coordinator._bus._unsubscribe == []
