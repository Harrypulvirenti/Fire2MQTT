"""Unit tests for the curated-app helpers (pure, no HA harness)."""
from __future__ import annotations

from custom_components.fire2mqtt.data import apps as apps_mod
from custom_components.fire2mqtt.data.apps import AppInfo, canonical_package, installed_curated


def _app(package: str, *aliases: str) -> AppInfo:
    return AppInfo(
        package=package,
        friendly_name="Acme",
        category="streaming",
        icon_mdi="mdi:alpha-a",
        alt_packages=tuple(aliases),
    )


def test_packages_property_lists_canonical_then_aliases():
    assert _app("com.acme", "com.acme.firetv").packages == ("com.acme", "com.acme.firetv")
    assert _app("com.acme").packages == ("com.acme",)


def test_installed_curated_matches_only_installed_real_apps():
    matched = installed_curated({"com.netflix.ninja", "org.jellyfin.androidtv", "com.unknown"})
    assert set(matched) == {"netflix", "jellyfin"}
    info, launch_package = matched["netflix"]
    assert info.friendly_name == "Netflix"
    assert launch_package == "com.netflix.ninja"


def test_canonical_package_passthrough_for_known_and_unknown():
    assert canonical_package("com.netflix.ninja") == "com.netflix.ninja"
    assert canonical_package("com.unknown.app") == "com.unknown.app"


def test_alias_canonicalizes_and_launches_the_installed_variant(monkeypatch):
    sample = {"acme": _app("com.acme", "com.acme.firetv")}
    monkeypatch.setattr(apps_mod, "CURATED_APPS", sample)
    monkeypatch.setattr(
        apps_mod,
        "PACKAGE_TO_KEY",
        {pkg: key for key, info in sample.items() for pkg in info.packages},
    )

    # An aliased foreground package resolves to the canonical key the rules use.
    assert apps_mod.canonical_package("com.acme.firetv") == "com.acme"

    # Present only under the alias → matched, and we launch the variant that's there.
    matched = apps_mod.installed_curated({"com.acme.firetv"})
    assert "acme" in matched
    _info, launch_package = matched["acme"]
    assert launch_package == "com.acme.firetv"
