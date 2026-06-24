"""Fire2MQTT media player entity."""
from __future__ import annotations

import datetime
import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from . import Fire2MqttConfigEntry
from .const import (
    CONF_IDLE_TIMEOUT,
    CONF_STATE_DETECTION_RULES_OVERRIDE,
    DEFAULT_IDLE_TIMEOUT,
    LAUNCHER_PACKAGES,
)
from .coordinator import Fire2MqttCoordinator
from .data.apps import canonical_package, installed_curated
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

# No TURN_ON/TURN_OFF: a sideloaded app can't wake the stick, and the TV powers on via the
# remote's IR (not CEC from the stick), so a power button here could never work. Control TV
# power via the TV's own HA integration / an IR blaster instead.
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Fire2MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    user_rules = entry.options.get(CONF_STATE_DETECTION_RULES_OVERRIDE, {})
    idle_timeout_min = entry.options.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT)
    async_add_entities([Fire2MqttMediaPlayer(coordinator, user_rules, idle_timeout_min)])


class Fire2MqttMediaPlayer(Fire2MqttEntity, MediaPlayerEntity):
    _attr_name = None  # device name IS the entity name
    _attr_device_class = MediaPlayerDeviceClass.TV

    def __init__(
        self,
        coordinator: Fire2MqttCoordinator,
        user_rules_override: dict,
        idle_timeout_min: float,
    ) -> None:
        super().__init__(coordinator, "media_player")
        self._user_rules = user_rules_override
        self._attr_supported_features = SUPPORTED_FEATURES
        self._idle_timeout = datetime.timedelta(minutes=idle_timeout_min)
        # Wall-clock time the current foreground package was first observed.
        # Tracked HA-side so a skewed device clock can't break standby detection.
        self._package_since: datetime.datetime | None = None
        self._last_package: str | None = None
        self._cancel_standby_timer: CALLBACK_TYPE | None = None

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_standby()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        package = self.coordinator.data.app.get("package", "")
        if package != self._last_package:
            self._last_package = package
            self._package_since = dt_util.utcnow()
            self._schedule_standby_check(package)
        super()._handle_coordinator_update()

    def _cancel_standby(self) -> None:
        if self._cancel_standby_timer is not None:
            self._cancel_standby_timer()
            self._cancel_standby_timer = None

    def _schedule_standby_check(self, package: str) -> None:
        """When the launcher comes to the foreground, re-render state once the
        idle timeout elapses so the entity flips to STANDBY without a new message."""
        self._cancel_standby()
        if package not in LAUNCHER_PACKAGES:
            return

        @callback
        def _expired(_now: datetime.datetime) -> None:
            self._cancel_standby_timer = None
            self.async_write_ha_state()

        self._cancel_standby_timer = async_call_later(
            self.hass, self._idle_timeout.total_seconds(), _expired
        )

    def _get_rules(self, package: str) -> list:
        # Resolve aliases (e.g. a Fire-TV-specific build) to the canonical package
        # the curated rules + any user override are keyed by, so detection still works.
        canonical = canonical_package(package)
        if canonical in self._user_rules:
            return self._user_rules[canonical]
        return CURATED_RULES.get(canonical, ["idle"])

    @property
    def state(self) -> MediaPlayerState:
        # Explicit screen-off report wins: the stick is asleep.
        if self.coordinator.data.screen.get("on") is False:
            return MediaPlayerState.OFF

        current_package = self.coordinator.data.app.get("package", "")
        if current_package in LAUNCHER_PACKAGES:
            if (
                self._package_since is not None
                and dt_util.utcnow() - self._package_since >= self._idle_timeout
            ):
                return MediaPlayerState.STANDBY
            return MediaPlayerState.IDLE

        playback = self.coordinator.data.playback
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
    def media_position_updated_at(self) -> datetime.datetime | None:
        """Without this HA treats media_position as frozen; the APK stamps
        every playback payload with epoch-ms ``ts``."""
        if self.coordinator.data.playback.get("position_ms") is None:
            return None
        ts = self.coordinator.data.playback.get("ts")
        if not ts:
            return None
        return dt_util.utc_from_timestamp(ts / 1000.0)

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
        # Prefer the curated friendly name when the foreground app is a known
        # installed app, so it lines up with an entry in source_list.
        package = self.coordinator.data.app.get("package", "")
        for info, launch_package in self._installed_apps().values():
            if package in info.packages:
                return info.friendly_name
        return self.coordinator.data.app.get("name")

    @property
    def source_list(self) -> list[str]:
        return sorted(info.friendly_name for info, _pkg in self._installed_apps().values())

    def _installed_apps(self) -> dict[str, tuple]:
        return installed_curated(self.coordinator.data.installed_packages)

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
        max_vol = vol.get("max") or 15
        await self.coordinator.async_set_volume(round(volume * max_vol))

    async def async_volume_up(self) -> None:
        await self.coordinator.async_volume_step(up=True)

    async def async_volume_down(self) -> None:
        await self.coordinator.async_volume_step(up=False)

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.async_mute_volume(mute)

    async def async_select_source(self, source: str) -> None:
        for info, launch_package in self._installed_apps().values():
            if info.friendly_name == source:
                await self.coordinator.async_launch_app(launch_package)
                return
        _LOGGER.warning("Fire2MQTT: unknown source '%s'", source)
