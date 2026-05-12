"""Tests for the Fire2MQTT coordinator."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.fire2mqtt.coordinator import Fire2MqttCoordinator


@pytest.fixture
def coordinator(hass):
    return Fire2MqttCoordinator(hass, topic_prefix="fire2mqtt", device_id="test_device")


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
    assert coordinator._topic("{prefix}/{device_id}/status") == "fire2mqtt/test_device/status"
