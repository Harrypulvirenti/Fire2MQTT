"""Fire2MQTT remote entity — sends key events via MQTT cmd/key."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity

_POWER_UNSUPPORTED = (
    "Fire TV power can't be controlled from the stick: a sideloaded app can't wake it, and "
    "the TV powers on via the remote's IR, not CEC. Control TV power via the TV's own Home "
    "Assistant integration or an IR blaster."
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([Fire2MqttRemote(coordinator)])


class Fire2MqttRemote(Fire2MqttEntity, RemoteEntity):
    _attr_name = "Remote"
    _attr_icon = "mdi:remote-tv"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "remote")

    @property
    def is_on(self) -> bool | None:
        """Mirror the screen state; None until the first screen payload arrives."""
        return self.coordinator.data.screen.get("on")

    async def async_turn_on(self, **kwargs: Any) -> None:
        # Power isn't controllable from the stick (see message); surface that plainly
        # instead of silently sending a command that does nothing.
        raise HomeAssistantError(_POWER_UNSUPPORTED)

    async def async_turn_off(self, **kwargs: Any) -> None:
        raise HomeAssistantError(_POWER_UNSUPPORTED)

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        num_repeats: int = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs: float = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        keys = [key.upper() for key in command]
        first = True
        for _ in range(num_repeats):
            for key in keys:
                if not first and delay_secs > 0:
                    await asyncio.sleep(delay_secs)
                first = False
                await self.coordinator.async_send_key(key)
