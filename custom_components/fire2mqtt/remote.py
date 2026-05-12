"""Fire2MQTT remote entity — sends key events via MQTT cmd/key."""
from __future__ import annotations

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity

ACTIVITY_LIST = [
    "HOME", "BACK", "MENU", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
    "DPAD_CENTER", "MEDIA_PLAY_PAUSE", "MEDIA_REWIND", "MEDIA_FAST_FORWARD",
    "VOLUME_UP", "VOLUME_DOWN", "MUTE",
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Fire2MqttCoordinator = entry.runtime_data.coordinator
    async_add_entities([Fire2MqttRemote(coordinator)])


class Fire2MqttRemote(Fire2MqttEntity, RemoteEntity):
    _attr_name = "Remote"
    _attr_icon = "mdi:remote-tv"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "remote")
        self._attr_activity_list = ACTIVITY_LIST

    async def async_send_command(self, command: list[str], **kwargs) -> None:
        for key in command:
            await self.coordinator.async_send_key(key.upper())
