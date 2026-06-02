"""Tests for the Fire2MQTT config flow and options flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import loader
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fire2mqtt.config_flow import Fire2MqttConfigFlow
from custom_components.fire2mqtt.const import (
    CONF_DEVICE_ID,
    CONF_ENABLED_APPS,
    CONF_IDLE_TIMEOUT,
    CONF_TOPIC_PREFIX,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)
from custom_components.fire2mqtt.data.apps import CURATED_APPS


# ── helpers ──────────────────────────────────────────────────────────────────

def _patch_mqtt_client(available: bool = True):
    return patch(
        "homeassistant.components.mqtt.async_wait_for_mqtt_client",
        AsyncMock(return_value=available),
    )


def _patch_apk_check(online: bool = True):
    return patch.object(
        Fire2MqttConfigFlow,
        "_check_apk_reachable",
        AsyncMock(return_value=online),
    )


@pytest.fixture(autouse=True)
async def _enable_custom(hass: HomeAssistant):
    """Allow HA to discover the custom integration in custom_components/."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)


VALID_INPUT = {
    "device_name": "Living Room",
    CONF_DEVICE_ID: "living_room",
    CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX,
}


# ── config flow ──────────────────────────────────────────────────────────────

async def test_form_shown_on_init(hass: HomeAssistant):
    with _patch_mqtt_client():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert not result.get("errors")


async def test_aborts_when_mqtt_not_configured(hass: HomeAssistant):
    with _patch_mqtt_client(available=False):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
    assert result["type"] == "abort"
    assert result["reason"] == "mqtt_not_configured"


async def test_invalid_device_id_shows_error(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check():
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input={**VALID_INPUT, CONF_DEVICE_ID: "Has Spaces!"},
        )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_DEVICE_ID) == "invalid_device_id"


async def test_valid_submission_creates_entry(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input=VALID_INPUT,
        )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"
    assert result["data"][CONF_TOPIC_PREFIX] == DEFAULT_TOPIC_PREFIX
    assert result["title"] == "Living Room"


async def test_apk_not_reachable_shows_error(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check(online=False):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input=VALID_INPUT,
        )
    assert result["type"] == "form"
    assert result["errors"].get("base") == "apk_not_reachable"


async def test_force_continue_bypasses_apk_error(hass: HomeAssistant):
    # Step 1: first submit → APK offline → form re-shown with _force_continue field
    with _patch_mqtt_client(), _patch_apk_check(online=False):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow_id = list(hass.config_entries.flow.async_progress())[0]["flow_id"]
        result = await hass.config_entries.flow.async_configure(flow_id, user_input=VALID_INPUT)
    assert result["type"] == "form"
    assert result["errors"].get("base") == "apk_not_reachable"

    # Step 2: re-submit with _force_continue=True → entry created despite offline APK
    with _patch_mqtt_client(), _patch_apk_check(online=False):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, "_force_continue": True}
        )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"


async def test_duplicate_device_id_aborts(hass: HomeAssistant):
    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    existing.add_to_hass(hass)

    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input=VALID_INPUT,
        )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


# ── options flow ──────────────────────────────────────────────────────────────

@pytest.fixture
def config_entry_with_options(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
        options={
            CONF_ENABLED_APPS: list(CURATED_APPS.keys()),
            CONF_IDLE_TIMEOUT: DEFAULT_IDLE_TIMEOUT,
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_options_flow_shows_form(hass: HomeAssistant, config_entry_with_options):
    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_options_flow_saves_selection(hass: HomeAssistant, config_entry_with_options):
    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix", "jellyfin"],
            CONF_IDLE_TIMEOUT: 5,
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENABLED_APPS] == ["netflix", "jellyfin"]
    assert result["data"][CONF_IDLE_TIMEOUT] == 5
