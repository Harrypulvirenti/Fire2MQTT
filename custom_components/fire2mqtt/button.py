"""Fire2MQTT button entities — one per enabled app launcher."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Fire2MqttConfigEntry
from .const import CONF_ENABLED_APPS, DOMAIN
from .coordinator import Fire2MqttCoordinator
from .data.apps import CURATED_APPS, AppInfo
from .entity import Fire2MqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    enabled_keys: list[str] = entry.options.get(CONF_ENABLED_APPS, list(CURATED_APPS.keys()))

    _remove_stale_buttons(hass, entry, coordinator.device_id, enabled_keys)

    buttons = [
        AppLaunchButton(coordinator, key, CURATED_APPS[key])
        for key in enabled_keys
        if key in CURATED_APPS
    ]
    async_add_entities(buttons)


def _remove_stale_buttons(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    device_id: str,
    enabled_keys: list[str],
) -> None:
    """Drop registry entries for launcher buttons that were disabled in options."""
    registry = er.async_get(hass)
    valid_unique_ids = {
        f"{DOMAIN}_{device_id}_launch_{key}" for key in enabled_keys if key in CURATED_APPS
    }
    prefix = f"{DOMAIN}_{device_id}_launch_"
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.domain != "button" or not reg_entry.unique_id.startswith(prefix):
            continue
        if reg_entry.unique_id not in valid_unique_ids:
            _LOGGER.debug("Removing stale launcher button %s", reg_entry.entity_id)
            registry.async_remove(reg_entry.entity_id)


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
