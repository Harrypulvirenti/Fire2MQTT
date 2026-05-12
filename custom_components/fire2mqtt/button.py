"""Fire2MQTT button entities — one per enabled app launcher."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLED_APPS
from .coordinator import Fire2MqttCoordinator
from .data.apps import CURATED_APPS, AppInfo
from .entity import Fire2MqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Fire2MqttCoordinator = entry.runtime_data.coordinator
    enabled_keys: list[str] = entry.options.get(CONF_ENABLED_APPS, list(CURATED_APPS.keys()))

    buttons = [
        AppLaunchButton(coordinator, key, CURATED_APPS[key])
        for key in enabled_keys
        if key in CURATED_APPS
    ]
    async_add_entities(buttons)


class AppLaunchButton(Fire2MqttEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: Fire2MqttCoordinator,
        app_key: str,
        app_info: AppInfo,
    ) -> None:
        super().__init__(coordinator, f"launch_{app_key}")
        self._app_key = app_key
        self._app_info = app_info
        self._attr_name = f"Launch {app_info.friendly_name}"
        self._attr_icon = app_info.icon_mdi

    async def async_press(self) -> None:
        await self.coordinator.async_launch_app(self._app_info.package)
