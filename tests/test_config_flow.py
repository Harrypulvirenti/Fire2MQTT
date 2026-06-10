"""Tests for the Fire2MQTT config flow and options flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
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


async def test_valid_submission_offers_provision_menu(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input=VALID_INPUT,
        )
    assert result["type"] == "menu"
    assert result["step_id"] == "provision"


async def test_skip_provision_creates_entry(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow_id = list(hass.config_entries.flow.async_progress())[0]["flow_id"]
        await hass.config_entries.flow.async_configure(flow_id, user_input=VALID_INPUT)
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={"next_step_id": "finish"}
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

    # Step 2: re-submit with _force_continue=True → provisioning menu (offline APK bypassed)
    with _patch_mqtt_client(), _patch_apk_check(online=False):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={**VALID_INPUT, "_force_continue": True}
        )
    assert result["type"] == "menu"
    assert result["step_id"] == "provision"


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


# ── ADB provisioning step ─────────────────────────────────────────────────────

async def _advance_to_provision_form(hass: HomeAssistant) -> str:
    """Drive the flow through user → provision menu → provision_adb form; return flow_id."""
    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow_id = list(hass.config_entries.flow.async_progress())[0]["flow_id"]
        await hass.config_entries.flow.async_configure(flow_id, user_input=VALID_INPUT)
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={"next_step_id": "provision_adb"}
        )
    assert result["type"] == "form"
    assert result["step_id"] == "provision_adb"
    return flow_id


async def test_provision_adb_success_creates_entry(hass: HomeAssistant):
    from custom_components.fire2mqtt.adb_provision import ProvisionResult

    flow_id = await _advance_to_provision_form(hass)
    with patch(
        "custom_components.fire2mqtt.adb_provision.async_provision",
        AsyncMock(return_value=ProvisionResult(installed=True, write_secure_settings=True)),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={"fire_tv_ip": "10.0.0.50"}
        )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == "living_room"


async def test_provision_adb_error_reshows_form(hass: HomeAssistant):
    from custom_components.fire2mqtt.adb_provision import ProvisionError

    flow_id = await _advance_to_provision_form(hass)
    with patch(
        "custom_components.fire2mqtt.adb_provision.async_provision",
        AsyncMock(side_effect=ProvisionError("adb_unreachable", "timeout")),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input={"fire_tv_ip": "10.0.0.50"}
        )
    assert result["type"] == "form"
    assert result["step_id"] == "provision_adb"
    assert result["errors"].get("base") == "adb_unreachable"


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


async def test_invalid_topic_prefix_shows_error(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check():
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input={**VALID_INPUT, CONF_TOPIC_PREFIX: "bad/#/prefix"},
        )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_TOPIC_PREFIX) == "invalid_topic_prefix"


async def test_nested_topic_prefix_accepted(hass: HomeAssistant):
    with _patch_mqtt_client(), _patch_apk_check(online=True):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            list(hass.config_entries.flow.async_progress())[0]["flow_id"],
            user_input={**VALID_INPUT, CONF_TOPIC_PREFIX: "home/media/fire2mqtt"},
        )
    assert result["type"] == "menu"


# ── reconfigure flow ──────────────────────────────────────────────────────────

async def test_reconfigure_updates_topic_prefix(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"

    with _patch_mqtt_client():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_TOPIC_PREFIX: "newprefix"}
        )
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TOPIC_PREFIX] == "newprefix"
    assert entry.data[CONF_DEVICE_ID] == "living_room"


async def test_reconfigure_rejects_invalid_prefix(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{DOMAIN}_living_room",
        data={CONF_DEVICE_ID: "living_room", CONF_TOPIC_PREFIX: DEFAULT_TOPIC_PREFIX},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOPIC_PREFIX: "nope+wild"}
    )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_TOPIC_PREFIX) == "invalid_topic_prefix"


# ── options: state detection rules override ──────────────────────────────────

async def test_options_flow_accepts_rules_override(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix"],
            CONF_IDLE_TIMEOUT: 10,
            CONF_STATE_DETECTION_RULES_OVERRIDE: '{"com.netflix.ninja": [{"playing": {"media_session_state": 3}}, "idle"]}',
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_STATE_DETECTION_RULES_OVERRIDE] == {
        "com.netflix.ninja": [{"playing": {"media_session_state": 3}}, "idle"]
    }


async def test_options_flow_rejects_bad_rules_override(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENABLED_APPS: ["netflix"],
            CONF_IDLE_TIMEOUT: 10,
            CONF_STATE_DETECTION_RULES_OVERRIDE: '["not", "a", "mapping"]',
        },
    )
    assert result["type"] == "form"
    assert result["errors"].get(CONF_STATE_DETECTION_RULES_OVERRIDE) == "invalid_rules_override"


async def test_options_flow_empty_rules_override_omitted(hass: HomeAssistant, config_entry_with_options):
    from custom_components.fire2mqtt.const import CONF_STATE_DETECTION_RULES_OVERRIDE

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLED_APPS: ["netflix"], CONF_IDLE_TIMEOUT: 10},
    )
    assert result["type"] == "create_entry"
    assert CONF_STATE_DETECTION_RULES_OVERRIDE not in result["data"]
