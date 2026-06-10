"""Fire2MQTT sensor entities."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .coordinator import Fire2MqttCoordinator
from .entity import Fire2MqttEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        CurrentAppSensor(coordinator),
        CurrentAppPackageSensor(coordinator),
        MediaTitleSensor(coordinator),
        MediaArtistSensor(coordinator),
        VolumeLevelSensor(coordinator),
        IpAddressSensor(coordinator),
    ])


class CurrentAppSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "Current App"
    _attr_icon = "mdi:television-play"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "current_app")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.app.get("name")

    @property
    def extra_state_attributes(self) -> dict:
        return {"package": self.coordinator.data.app.get("package")}


class CurrentAppPackageSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "Current App Package"
    _attr_icon = "mdi:package-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "current_app_package")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.app.get("package")


class MediaTitleSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "Media Title"
    _attr_icon = "mdi:text"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "media_title")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.playback.get("title")


class MediaArtistSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "Media Artist"
    _attr_icon = "mdi:microphone"

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "media_artist")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.playback.get("artist")


class VolumeLevelSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "Volume Level"
    _attr_icon = "mdi:volume-high"
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "volume_level")

    @property
    def native_value(self) -> int | None:
        vol = self.coordinator.data.volume
        if vol.get("max") and vol.get("level") is not None:
            return round(vol["level"] / vol["max"] * 100)
        return None

    @property
    def extra_state_attributes(self) -> dict:
        vol = self.coordinator.data.volume
        return {
            "raw_level": vol.get("level"),
            "max_level": vol.get("max"),
            "muted": vol.get("mute"),
        }


class IpAddressSensor(Fire2MqttEntity, SensorEntity):
    _attr_name = "IP Address"
    _attr_icon = "mdi:ip-network"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: Fire2MqttCoordinator) -> None:
        super().__init__(coordinator, "ip_address")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.device_info.get("ip") or None
