"""Fire2MQTT binary sensor entities."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Fire2MqttCoordinator = entry.runtime_data.coordinator
    async_add_entities([
        ScreenOnSensor(coordinator),
    ])


class ScreenOnSensor(Fire2MqttEntity, BinarySensorEntity):
    _attr_name = "Screen"
    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "screen")

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.screen.get("on")
