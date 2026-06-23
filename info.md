# Fire2MQTT

**Real-time Fire TV Stick state in Home Assistant, over MQTT.**

A sideloaded companion app on your Fire Stick publishes state changes the moment they
happen — Home Assistant subscribes and exposes proper entities. No ADB polling, no
5-second lag. State is push-only and arrives in well under 100 ms.

## What you get (per Fire Stick)

- **Media player** — playback state (incl. off/standby), title, position, source select, volume, power
- **Sensors** — current app, media title/artist, volume level, IP address
- **Binary sensors** — screen on/off, APK online/offline
- **Buttons** — one-tap launch for curated streaming apps
- **Remote** — send key events (HOME, BACK, DPAD, …) and power

Correct `playing` / `paused` / `idle` detection out of the box for Netflix, Prime Video,
YouTube, Disney+, Crunchyroll, Jellyfin, Plex, Emby, Spotify, Twitch, Max, Apple TV and Kodi.

Add one config entry per stick — each gets its own device, entities, and MQTT topic
namespace, so multiple sticks coexist cleanly on one broker.

## Setup

1. Install **Fire2MQTT** from HACS and restart Home Assistant.
2. Settings → Devices & Services → **Add Integration** → search **Fire2MQTT**.
3. Choose how to get the app onto your Fire TV — automatically over ADB, or sideload it
   yourself — then enter the device name and ID.

> **Prerequisite:** the MQTT integration must be configured first; Fire2MQTT uses your
> existing broker.

Full documentation, the architecture diagram, and example automations are in the
[README](https://github.com/Harrypulvirenti/Fire2MQTT#readme).
