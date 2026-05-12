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
}

# Reverse lookup: package → app key
PACKAGE_TO_KEY: dict[str, str] = {
    info.package: key for key, info in CURATED_APPS.items()
}
