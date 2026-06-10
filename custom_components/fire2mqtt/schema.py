"""Schema / payload models for Fire2MQTT MQTT messages.

Each payload class is a frozen dataclass declaring the canonical fields for
that topic.  The ``from_raw`` classmethod validates and coerces an already-
parsed dict, drops unknown keys, fills defaults for missing fields, and
returns a **plain normalised dict** so that ``coordinator.data.*`` remains a
plain ``dict`` (as entity files expect).

Coercion policy
---------------
- Known field: coerce to declared type; on failure log a warning, use default.
- Unknown key: silently dropped.
- Missing optional field: fill with ``None``.
- Missing required field: fill with type-appropriate zero-value.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .const import MAX_PAYLOAD_STR_LENGTH, SCHEMA_VERSION

# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------

def _coerce_int(
    value: Any,
    field: str,
    default: int | None,
    logger: logging.Logger | None,
) -> int | None:
    """Return *value* coerced to int, or *default* on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        if logger:
            logger.warning(
                "Fire2MQTT schema: cannot coerce field %r value %r to int; using default %r",
                field,
                value,
                default,
            )
        return default


def _coerce_str(
    value: Any,
    field: str,
    default: str | None,
    logger: logging.Logger | None,
) -> str | None:
    """Return *value* coerced to str, or *default* on failure.

    Strings are capped at MAX_PAYLOAD_STR_LENGTH (HA's state length limit) so
    an oversized MQTT payload cannot break entity updates or bloat the recorder.
    """
    if value is None:
        return default
    try:
        coerced = str(value)
    except (TypeError, ValueError):
        if logger:
            logger.warning(
                "Fire2MQTT schema: cannot coerce field %r value %r to str; using default %r",
                field,
                value,
                default,
            )
        return default
    if len(coerced) > MAX_PAYLOAD_STR_LENGTH:
        if logger:
            logger.warning(
                "Fire2MQTT schema: field %r value truncated from %d to %d chars",
                field,
                len(coerced),
                MAX_PAYLOAD_STR_LENGTH,
            )
        coerced = coerced[:MAX_PAYLOAD_STR_LENGTH]
    return coerced


def _coerce_bool(
    value: Any,
    field: str,
    default: bool,
    logger: logging.Logger | None,
) -> bool:
    """Return *value* coerced to bool, or *default* on failure.

    Accepts: bool, int (0/1), and strings "true"/"false"/"1"/"0".
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
    if logger:
        logger.warning(
            "Fire2MQTT schema: cannot coerce field %r value %r to bool; using default %r",
            field,
            value,
            default,
        )
    return default


# ---------------------------------------------------------------------------
# Payload models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlaybackPayload:
    """Models the ``state/playback`` MQTT topic payload."""

    media_session_state: int = 0
    app: str = ""
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    duration_ms: int | None = None
    position_ms: int | None = None
    ts: int = 0
    # Optional fields present in some APK versions
    audio_state: str | None = None
    wake_lock_size: int | None = None

    @classmethod
    def from_raw(
        cls,
        raw: dict,
        *,
        logger: logging.Logger | None = None,
    ) -> dict:
        """Validate/coerce *raw* and return a plain normalised dict."""
        return {
            "media_session_state": _coerce_int(
                raw.get("media_session_state"), "media_session_state", 0, logger
            ),
            "app": _coerce_str(raw.get("app"), "app", "", logger) or "",
            "title": _coerce_str(raw.get("title"), "title", None, logger),
            "artist": _coerce_str(raw.get("artist"), "artist", None, logger),
            "album": _coerce_str(raw.get("album"), "album", None, logger),
            "duration_ms": _coerce_int(raw.get("duration_ms"), "duration_ms", None, logger),
            "position_ms": _coerce_int(raw.get("position_ms"), "position_ms", None, logger),
            "ts": _coerce_int(raw.get("ts"), "ts", 0, logger) or 0,
            "audio_state": _coerce_str(raw.get("audio_state"), "audio_state", None, logger),
            "wake_lock_size": _coerce_int(raw.get("wake_lock_size"), "wake_lock_size", None, logger),
        }


@dataclass(frozen=True)
class AppPayload:
    """Models the ``state/app`` MQTT topic payload."""

    package: str = ""
    name: str = ""
    ts: int = 0

    @classmethod
    def from_raw(
        cls,
        raw: dict,
        *,
        logger: logging.Logger | None = None,
    ) -> dict:
        """Validate/coerce *raw* and return a plain normalised dict."""
        return {
            "package": _coerce_str(raw.get("package"), "package", "", logger) or "",
            "name": _coerce_str(raw.get("name"), "name", "", logger) or "",
            "ts": _coerce_int(raw.get("ts"), "ts", 0, logger) or 0,
        }


@dataclass(frozen=True)
class ScreenPayload:
    """Models the ``state/screen`` MQTT topic payload."""

    on: bool = False
    ts: int = 0

    @classmethod
    def from_raw(
        cls,
        raw: dict,
        *,
        logger: logging.Logger | None = None,
    ) -> dict:
        """Validate/coerce *raw* and return a plain normalised dict."""
        return {
            "on": _coerce_bool(raw.get("on"), "on", False, logger),
            "ts": _coerce_int(raw.get("ts"), "ts", 0, logger) or 0,
        }


@dataclass(frozen=True)
class VolumePayload:
    """Models the ``state/volume`` MQTT topic payload."""

    level: int = 0
    max: int = 0
    mute: bool = False
    ts: int = 0

    @classmethod
    def from_raw(
        cls,
        raw: dict,
        *,
        logger: logging.Logger | None = None,
    ) -> dict:
        """Validate/coerce *raw* and return a plain normalised dict."""
        return {
            "level": _coerce_int(raw.get("level"), "level", 0, logger) or 0,
            "max": _coerce_int(raw.get("max"), "max", 0, logger) or 0,
            "mute": _coerce_bool(raw.get("mute"), "mute", False, logger),
            "ts": _coerce_int(raw.get("ts"), "ts", 0, logger) or 0,
        }


@dataclass(frozen=True)
class DevicePayload:
    """Models the ``state/device`` MQTT topic payload."""

    model: str = ""
    fire_os: str = ""
    ip: str = ""
    mac: str = ""
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_raw(
        cls,
        raw: dict,
        *,
        logger: logging.Logger | None = None,
    ) -> dict:
        """Validate/coerce *raw* and return a plain normalised dict.

        Logs a warning when ``schema_version`` does not match
        :data:`~custom_components.fire2mqtt.const.SCHEMA_VERSION`.
        """
        schema_ver = _coerce_int(
            raw.get("schema_version"), "schema_version", SCHEMA_VERSION, logger
        )
        if schema_ver is None:
            schema_ver = SCHEMA_VERSION
        if schema_ver != SCHEMA_VERSION:
            if logger:
                logger.warning(
                    "Fire2MQTT schema: device reports schema_version=%d but integration "
                    "expects %d — update the APK or the integration.",
                    schema_ver,
                    SCHEMA_VERSION,
                )
        return {
            "model": _coerce_str(raw.get("model"), "model", "", logger) or "",
            "fire_os": _coerce_str(raw.get("fire_os"), "fire_os", "", logger) or "",
            "ip": _coerce_str(raw.get("ip"), "ip", "", logger) or "",
            "mac": _coerce_str(raw.get("mac"), "mac", "", logger) or "",
            "schema_version": schema_ver,
        }
