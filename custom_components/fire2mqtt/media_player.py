"""Fire2MQTT media player entity."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_STATE_DETECTION_RULES_OVERRIDE,
    DOMAIN,
    TOPIC_CMD_LAUNCH,
    TOPIC_CMD_MEDIA,
    TOPIC_CMD_POWER,
    TOPIC_CMD_VOLUME,
)
from .coordinator import Fire2MqttCoordinator
from .data.rules import CURATED_RULES
from .entity import Fire2MqttEntity
from .state_detection import evaluate

_LOGGER = logging.getLogger(__name__)

_HA_STATE_MAP = {
    "playing": MediaPlayerState.PLAYING,
    "paused": MediaPlayerState.PAUSED,
    "idle": MediaPlayerState.IDLE,
    "standby": MediaPlayerState.STANDBY,
    "off": MediaPlayerState.OFF,
}

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.TURN_OFF
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: Fire2MqttCoordinator = entry.runtime_data.coordinator
    user_rules = entry.options.get(CONF_STATE_DETECTION_RULES_OVERRIDE, {})
    async_add_entities([Fire2MqttMediaPlayer(coordinator, user_rules)])


class Fire2MqttMediaPlayer(Fire2MqttEntity, MediaPlayerEntity):
    _attr_name = None  # device name IS the entity name

    def __init__(
        self,
        coordinator: Fire2MqttCoordinator,
        user_rules_override: dict,
    ) -> None:
        super().__init__(coordinator, "media_player")
        self._user_rules = user_rules_override
        self._attr_supported_features = SUPPORTED_FEATURES

    def _get_rules(self, package: str) -> list:
        if package in self._user_rules:
            return self._user_rules[package]
        return CURATED_RULES.get(package, ["idle"])

    @property
    def state(self) -> MediaPlayerState:
        playback = self.coordinator.data.playback
        current_package = self.coordinator.data.app.get("package", "")
        rules = self._get_rules(current_package)
        detected = evaluate(rules, playback)
        return _HA_STATE_MAP.get(detected or "idle", MediaPlayerState.IDLE)

    @property
    def media_title(self) -> str | None:
        return self.coordinator.data.playback.get("title")

    @property
    def media_artist(self) -> str | None:
        return self.coordinator.data.playback.get("artist")

    @property
    def media_album_name(self) -> str | None:
        return self.coordinator.data.playback.get("album")

    @property
    def media_duration(self) -> float | None:
        ms = self.coordinator.data.playback.get("duration_ms")
        return ms / 1000.0 if ms else None

    @property
    def media_position(self) -> float | None:
        ms = self.coordinator.data.playback.get("position_ms")
        return ms / 1000.0 if ms else None

    @property
    def app_id(self) -> str | None:
        return self.coordinator.data.app.get("package")

    @property
    def app_name(self) -> str | None:
        return self.coordinator.data.app.get("name")

    @property
    def volume_level(self) -> float | None:
        vol = self.coordinator.data.volume
        if vol.get("max") and vol.get("level") is not None:
            return vol["level"] / vol["max"]
        return None

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.data.volume.get("mute")

    @property
    def source(self) -> str | None:
        return self.coordinator.data.app.get("name")

    @property
    def source_list(self) -> list[str]:
        from .data.apps import CURATED_APPS
        return [info.friendly_name for info in CURATED_APPS.values()]

    async def async_media_play(self) -> None:
        await self.coordinator.async_media_command("play")

    async def async_media_pause(self) -> None:
        await self.coordinator.async_media_command("pause")

    async def async_media_stop(self) -> None:
        await self.coordinator.async_media_command("stop")

    async def async_media_next_track(self) -> None:
        await self.coordinator.async_media_command("next")

    async def async_media_previous_track(self) -> None:
        await self.coordinator.async_media_command("prev")

    async def async_set_volume_level(self, volume: float) -> None:
        vol = self.coordinator.data.volume
        max_vol = vol.get("max", 15)
        await self.coordinator.async_set_volume(round(volume * max_vol))

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.async_mute_volume(mute)

    async def async_select_source(self, source: str) -> None:
        from .data.apps import CURATED_APPS
        for key, info in CURATED_APPS.items():
            if info.friendly_name == source:
                await self.coordinator.async_launch_app(info.package)
                return
        _LOGGER.warning("Fire2MQTT: unknown source '%s'", source)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_send_command(TOPIC_CMD_POWER, "sleep")
