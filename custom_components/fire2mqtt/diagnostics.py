"""Diagnostics support for Fire2MQTT."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import Fire2MqttConfigEntry

TO_REDACT = {"ip", "mac"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: Fire2MqttConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "state": {
            "online": coordinator.data.online,
            "playback": coordinator.data.playback,
            "app": coordinator.data.app,
            "screen": coordinator.data.screen,
            "volume": coordinator.data.volume,
            "device": async_redact_data(coordinator.data.device_info, TO_REDACT),
        },
    }
