"""Fire2MQTT — Fire TV Stick → MQTT → Home Assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_DEVICE_ID,
    CONF_TOPIC_PREFIX,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import Fire2MqttCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class Fire2MqttRuntimeData:
    coordinator: Fire2MqttCoordinator


type Fire2MqttConfigEntry = ConfigEntry[Fire2MqttRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: Fire2MqttConfigEntry) -> bool:
    device_id = entry.data[CONF_DEVICE_ID]
    prefix = entry.data.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX)

    coordinator = Fire2MqttCoordinator(hass, entry, prefix, device_id)
    await coordinator.async_setup()

    entry.runtime_data = Fire2MqttRuntimeData(coordinator=coordinator)

    _purge_legacy_buttons(hass, entry, device_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Fire2MqttConfigEntry) -> bool:
    await entry.runtime_data.coordinator.async_teardown()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: Fire2MqttConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _purge_legacy_buttons(
    hass: HomeAssistant, entry: Fire2MqttConfigEntry, device_id: str
) -> None:
    """Remove the per-app launch Button entities from before the launcher was
    replaced by a single select entity, so they don't linger as unavailable."""
    registry = er.async_get(hass)
    prefix = f"{DOMAIN}_{device_id}_launch_"
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.domain == "button" and reg_entry.unique_id.startswith(prefix):
            _LOGGER.debug("Removing legacy launcher button %s", reg_entry.entity_id)
            registry.async_remove(reg_entry.entity_id)
