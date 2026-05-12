"""Base entity for Fire2MQTT."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import Fire2MqttCoordinator


class Fire2MqttEntity(CoordinatorEntity[Fire2MqttCoordinator]):
    """Base class for all Fire2MQTT entities.

    Provides device_info derived from the coordinator's cached device payload,
    and a consistent unique_id prefix based on device_id.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: Fire2MqttCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._device_id = coordinator._device_id
        self._attr_unique_id = f"{DOMAIN}_{self._device_id}_{unique_suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        device = self.coordinator.data.device_info
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("model", f"Fire TV {self._device_id}"),
            manufacturer="Amazon",
            model=device.get("model"),
            sw_version=device.get("fire_os"),
            configuration_url=None,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data.online
