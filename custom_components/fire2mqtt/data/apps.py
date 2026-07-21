"""Curated app database for Fire TV devices.

Each entry maps a short key to metadata used by the integration.
The `package` field is the authoritative Android package name.
The `icon_mdi` field is a Material Design icon name (used in button entities).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppInfo:
    package: str
    friendly_name: str
    category: str
    icon_mdi: str
    # Extra package names the same app ships under (e.g. an Amazon-appstore Fire TV
    # build vs the Play build). Any of these counting as "installed"/foreground, but
    # `package` stays the canonical key for CURATED_RULES and icons.
    alt_packages: tuple[str, ...] = ()

    @property
    def packages(self) -> tuple[str, ...]:
        """Canonical package first, then any known aliases."""
        return (self.package, *self.alt_packages)


CURATED_APPS: dict[str, AppInfo] = {
    "crunchyroll": AppInfo(
        package="com.crunchyroll.crunchyroid",
        friendly_name="Crunchyroll",
        category="streaming",
        icon_mdi="mdi:television-play",
    ),
    "netflix": AppInfo(
        package="com.netflix.ninja",
        friendly_name="Netflix",
        category="streaming",
        icon_mdi="mdi:netflix",
    ),
    "prime_video": AppInfo(
        package="com.amazon.avod.thirdpartyclient",
        friendly_name="Prime Video",
        category="streaming",
        icon_mdi="mdi:amazon",
        # Fire TV ships Prime Video as its integrated build, not the third-party
        # client: newer Fire OS uses com.amazon.firebat (PVFTV-*), older devices
        # com.amazon.avod. Alias both so foreground detection + rules resolve.
        alt_packages=("com.amazon.firebat", "com.amazon.avod"),
    ),
    "f1_tv": AppInfo(
        package="com.formulaone.production",
        friendly_name="F1 TV",
        category="streaming",
        icon_mdi="mdi:flag-checkered",
    ),
    "youtube": AppInfo(
        package="com.amazon.firetv.youtube",
        friendly_name="YouTube",
        category="streaming",
        icon_mdi="mdi:youtube",
    ),
    "disney_plus": AppInfo(
        package="com.disney.disneyplus",
        friendly_name="Disney+",
        category="streaming",
        icon_mdi="mdi:television-play",
    ),
    "jellyfin": AppInfo(
        package="org.jellyfin.androidtv",
        friendly_name="Jellyfin",
        category="self_hosted",
        icon_mdi="mdi:jellyfish",
    ),
    "plex": AppInfo(
        package="com.plexapp.android",
        friendly_name="Plex",
        category="self_hosted",
        icon_mdi="mdi:plex",
    ),
    "emby": AppInfo(
        package="tv.emby.embyatv",
        friendly_name="Emby",
        category="self_hosted",
        icon_mdi="mdi:television-play",
    ),
    "spotify": AppInfo(
        package="com.spotify.music",
        friendly_name="Spotify",
        category="music",
        icon_mdi="mdi:spotify",
    ),
    "twitch": AppInfo(
        package="tv.twitch.android.app",
        friendly_name="Twitch",
        category="streaming",
        icon_mdi="mdi:twitch",
    ),
    "hbo_max": AppInfo(
        package="com.hbo.hbonow",
        friendly_name="Max (HBO)",
        category="streaming",
        icon_mdi="mdi:television-play",
    ),
    "apple_tv": AppInfo(
        package="com.apple.atve.amazon.appletv",
        friendly_name="Apple TV",
        category="streaming",
        icon_mdi="mdi:apple",
    ),
    "kodi": AppInfo(
        package="org.xbmc.kodi",
        friendly_name="Kodi",
        category="self_hosted",
        icon_mdi="mdi:kodi",
    ),
    "wholphin": AppInfo(
        package="com.github.damontecres.wholphin",
        friendly_name="Wholphin",
        category="self_hosted",
        icon_mdi="mdi:dolphin",
    ),
    "nuvio": AppInfo(
        package="com.nuvio.tv",
        friendly_name="Nuvio",
        category="streaming",
        icon_mdi="mdi:television-play",
    ),
}

# Reverse lookup: every known package (canonical + aliases) → app key
PACKAGE_TO_KEY: dict[str, str] = {
    pkg: key for key, info in CURATED_APPS.items() for pkg in info.packages
}


def canonical_package(package: str) -> str:
    """Map any known alias to the curated canonical package (the key CURATED_RULES
    uses); pass unknown packages through unchanged. Lets state detection resolve an
    aliased foreground package (e.g. a Fire-TV-specific build) to its rules."""
    key = PACKAGE_TO_KEY.get(package)
    return CURATED_APPS[key].package if key else package


def installed_curated(installed: set[str]) -> dict[str, tuple[AppInfo, str]]:
    """Curated apps that have at least one of their packages installed.

    Returns ``{app_key: (info, launch_package)}`` where ``launch_package`` is the
    actual installed package to send to ``cmd/launch`` — so an app present under an
    alias launches the build that's really there.
    """
    result: dict[str, tuple[AppInfo, str]] = {}
    for key, info in CURATED_APPS.items():
        match = next((pkg for pkg in info.packages if pkg in installed), None)
        if match is not None:
            result[key] = (info, match)
    return result
