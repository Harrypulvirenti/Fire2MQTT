"""Tests for the optional ADB provisioning module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fire2mqtt.adb_provision import (
    ProvisionError,
    async_provision,
)
from custom_components.fire2mqtt.const import FIRE2MQTT_PACKAGE


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

    result = await async_provision(hass, "10.0.0.50")

    assert result.installed is False
    assert result.write_secure_settings is True
    assert result.launched is True
    device.push.assert_not_called()
    assert any("am start" in c.args[0] for c in device.shell.call_args_list)


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
        result = await async_provision(hass, "10.0.0.50")

    assert result.installed is True
    device.push.assert_awaited_once()


async def test_provision_grant_failed_raises(hass: HomeAssistant, _patch_adb_imports):
    device = _fake_device({
        f"pm list packages {FIRE2MQTT_PACKAGE}": f"package:{FIRE2MQTT_PACKAGE}",
        "dumpsys package": "android.permission.WRITE_SECURE_SETTINGS: granted=false",
    })
    _patch_adb_imports["device"] = device

    with pytest.raises(ProvisionError) as exc:
        await async_provision(hass, "10.0.0.50")
    assert exc.value.reason == "grant_failed"
    device.close.assert_awaited()
