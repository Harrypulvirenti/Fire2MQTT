"""Tests for the optional ADB provisioning module."""
from __future__ import annotations

import shlex
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fire2mqtt.adb_provision import (
    BrokerConfig,
    ProvisionError,
    _build_launch_cmd,
    async_provision,
)
from custom_components.fire2mqtt.const import FIRE2MQTT_LAUNCH_COMPONENT, FIRE2MQTT_PACKAGE


def _cfg(**overrides) -> BrokerConfig:
    base = dict(
        host="192.168.1.10",
        port=1883,
        username="user",
        password="pass",
        device_id="living_room",
        topic_prefix="fire2mqtt",
        use_tls=False,
    )
    base.update(overrides)
    return BrokerConfig(**base)


def _fake_device(shell_map: dict[str, str]) -> MagicMock:
    """Build a fake AdbDeviceTcpAsync whose shell() returns canned output by substring match."""
    device = MagicMock()
    device.connect = AsyncMock()
    device.close = AsyncMock()
    device.push = AsyncMock()

    async def _shell(cmd: str, *args, **kwargs) -> str:
        for needle, out in shell_map.items():
            if needle in cmd:
                return out
        return ""

    device.shell = AsyncMock(side_effect=_shell)
    return device


@pytest.fixture
def _patch_adb_imports():
    """Patch the lazily-imported adb_shell symbols inside async_provision."""
    device_holder: dict = {}

    class _FakeTcp:
        def __init__(self, *a, **k):
            self._d = device_holder["device"]

        def __new__(cls, *a, **k):  # return the prebuilt fake instead of a real device
            return device_holder["device"]

    with patch.dict(
        "sys.modules",
        {
            "adb_shell.adb_device_async": MagicMock(AdbDeviceTcpAsync=_FakeTcp),
            "adb_shell.auth.keygen": MagicMock(keygen=MagicMock()),
            "adb_shell.auth.sign_pythonrsa": MagicMock(
                PythonRSASigner=MagicMock(FromRSAKeyPath=MagicMock(return_value="signer"))
            ),
            "adb_shell.exceptions": MagicMock(
                DeviceAuthError=type("DeviceAuthError", (Exception,), {}),
                TcpTimeoutException=type("TcpTimeoutException", (Exception,), {}),
            ),
        },
    ):
        yield device_holder


async def test_provision_already_installed_grants_and_launches(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": f"android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    result = await async_provision(hass, "10.0.0.50", _cfg())

    assert result.installed is False
    assert result.write_secure_settings is True
    assert result.launched is True
    device.push.assert_not_called()
    # The launch carries the broker config as extras.
    launch = next(c.args[0] for c in device.shell.call_args_list if "am start" in c.args[0])
    assert "--es broker_host 192.168.1.10" in launch
    assert "--es device_id living_room" in launch


async def test_provision_downloads_and_installs_when_missing(
    hass: HomeAssistant, _patch_adb_imports
):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": "",  # not installed
        "pm install": "Success",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=true",
    })
    _patch_adb_imports["device"] = device

    with patch(
        "custom_components.fire2mqtt.adb_provision._async_download_apk",
        AsyncMock(return_value="/tmp/fire2mqtt.apk"),
    ):
        result = await async_provision(hass, "10.0.0.50", _cfg())

    assert result.installed is True
    device.push.assert_awaited_once()


async def test_provision_grant_failed_raises(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=false",
    })
    _patch_adb_imports["device"] = device

    with pytest.raises(ProvisionError) as exc:
        await async_provision(hass, "10.0.0.50", _cfg())
    assert exc.value.reason == "grant_failed"
    device.close.assert_awaited()


# ── pure launch-command builder ───────────────────────────────────────────────

def test_build_launch_cmd_includes_all_extras():
    cmd = _build_launch_cmd(FIRE2MQTT_LAUNCH_COMPONENT, _cfg())
    assert cmd.startswith(f"am start -n {FIRE2MQTT_LAUNCH_COMPONENT}")
    for fragment in (
        "--es broker_host 192.168.1.10",
        "--es broker_port 1883",
        "--es broker_username user",
        "--es broker_password pass",
        "--es device_id living_room",
        "--es topic_prefix fire2mqtt",
        "--es use_tls false",
    ):
        assert fragment in cmd, fragment


def test_build_launch_cmd_serializes_tls_as_bool_string():
    assert "--es use_tls true" in _build_launch_cmd("comp", _cfg(use_tls=True, port=8883))


def test_build_launch_cmd_quotes_password_with_shell_metacharacters():
    # A password with a space and a quote must survive device.shell() tokenization intact.
    secret = "p@ss word'!$x"
    cmd = _build_launch_cmd("comp", _cfg(password=secret))
    assert shlex.quote(secret) in cmd
    tokens = shlex.split(cmd)
    assert tokens[tokens.index("broker_password") + 1] == secret
