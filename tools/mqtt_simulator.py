#!/usr/bin/env python3
"""Fire2MQTT MQTT Simulator

Publishes realistic state payloads to your MQTT broker, simulating a Fire TV Stick
running the Fire2MQTT APK. Use this to develop/test the HA integration without
needing a physical device.

Usage:
    python3 tools/mqtt_simulator.py --device-id living_room_fire_tv --broker 192.168.1.10
    python3 tools/mqtt_simulator.py --help
"""
import argparse
import json
import time
import threading
import sys

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Install paho-mqtt: pip install paho-mqtt")
    sys.exit(1)


DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_PREFIX = "fire2mqtt"
DEFAULT_DEVICE_ID = "simulated_fire_tv"

APPS = [
    {"package": "com.crunchyroll.crunchyroid", "name": "Crunchyroll"},
    {"package": "com.netflix.ninja", "name": "Netflix"},
    {"package": "com.amazon.avod.thirdpartyclient", "name": "Prime Video"},
    {"package": "com.amazon.firetv.youtube", "name": "YouTube"},
    {"package": "dev.amazon.ignite", "name": "Fire TV Home"},
]

PLAYBACK_SEQUENCE = [
    # (media_session_state, title, artist, duration_ms, position_ms, sleep_secs)
    (0, None, None, None, None, 2),          # idle on home
    (3, "Demon Slayer S4E01", None, 1380000, 0, 3),     # playing
    (3, "Demon Slayer S4E01", None, 1380000, 60000, 2),  # playing, 1min in
    (2, "Demon Slayer S4E01", None, 1380000, 120000, 3), # paused
    (3, "Demon Slayer S4E01", None, 1380000, 120000, 3), # resumed
    (1, None, None, None, None, 2),          # stopped
    (0, None, None, None, None, 2),          # idle
]


def ts() -> int:
    return int(time.time() * 1000)


def publish(client: mqtt.Client, prefix: str, device_id: str, subtopic: str, payload: dict | str, retain: bool = True):
    topic = f"{prefix}/{device_id}/{subtopic}"
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    client.publish(topic, raw, retain=retain, qos=1)
    print(f"  → {topic}: {raw[:120]}")


def run_simulation(args):
    client = mqtt.Client(client_id=f"fire2mqtt_simulator_{args.device_id}")
    if args.username:
        client.username_pw_set(args.username, args.password)

    # LWT
    client.will_set(
        f"{args.prefix}/{args.device_id}/status",
        "offline",
        retain=True,
        qos=1,
    )

    client.connect(args.broker, args.port)
    client.loop_start()

    print(f"\nFire2MQTT Simulator")
    print(f"Device ID : {args.device_id}")
    print(f"Broker    : {args.broker}:{args.port}")
    print(f"Prefix    : {args.prefix}")
    print(f"Press Ctrl+C to stop\n")

    # Publish device info + online
    publish(client, args.prefix, args.device_id, "status", "online")
    publish(client, args.prefix, args.device_id, "state/device", {
        "model": "Fire TV Stick 4K (Simulated)",
        "fire_os": "8.2.2.1",
        "ip": "127.0.0.1",
        "mac": "de:ad:be:ef:00:01",
        "schema_version": 2,
    })
    # Installed-apps inventory: everything in APPS except the launcher home.
    publish(client, args.prefix, args.device_id, "state/apps", {
        "packages": [a["package"] for a in APPS if a["package"] != "dev.amazon.ignite"],
        "ts": ts(),
    })
    publish(client, args.prefix, args.device_id, "state/screen", {"on": True, "ts": ts()})
    publish(client, args.prefix, args.device_id, "state/volume", {"level": 8, "max": 15, "mute": False, "ts": ts()})

    app_idx = 0
    app = APPS[app_idx]

    print(f"App: {app['name']} ({app['package']})")
    publish(client, args.prefix, args.device_id, "state/app", {"package": app["package"], "name": app["name"], "ts": ts()})

    step_idx = 0
    try:
        while True:
            state, title, artist, duration, position, sleep = PLAYBACK_SEQUENCE[step_idx % len(PLAYBACK_SEQUENCE)]

            payload = {
                "media_session_state": state,
                "app": app["package"],
                "ts": ts(),
            }
            if title:
                payload["title"] = title
            if artist:
                payload["artist"] = artist
            if duration is not None:
                payload["duration_ms"] = duration
            if position is not None:
                payload["position_ms"] = position

            print(f"\n[state {state}] {title or '—'}")
            publish(client, args.prefix, args.device_id, "state/playback", payload)

            # Cycle to next app after a full sequence
            step_idx += 1
            if step_idx % len(PLAYBACK_SEQUENCE) == 0:
                app_idx = (app_idx + 1) % len(APPS)
                app = APPS[app_idx]
                print(f"\n→ Switching app to {app['name']}")
                publish(client, args.prefix, args.device_id, "state/app", {
                    "package": app["package"],
                    "name": app["name"],
                    "ts": ts(),
                })

            time.sleep(sleep)

    except KeyboardInterrupt:
        print("\n\nSimulator stopped.")
        publish(client, args.prefix, args.device_id, "status", "offline")
        client.loop_stop()
        client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Fire2MQTT MQTT Simulator")
    parser.add_argument("--broker", default=DEFAULT_BROKER)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, dest="device_id")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()
    run_simulation(args)


if __name__ == "__main__":
    main()
