#!/usr/bin/env python3
"""Fire2MQTT MQTT Monitor

Subscribes to all Fire2MQTT topics and pretty-prints every message in real time.
Use this to verify what the APK is publishing without needing Home Assistant.

Usage:
    python3 tools/mqtt_monitor.py --broker 192.168.1.10
    python3 tools/mqtt_monitor.py --broker 192.168.1.10 --username myuser --password mypass
    python3 tools/mqtt_monitor.py --help
"""
import argparse
import json
import sys
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Install paho-mqtt: pip install paho-mqtt")
    sys.exit(1)

DEFAULT_PORT = 1883
DEFAULT_PREFIX = "fire2mqtt"

TOPIC_COLORS = {
    "state/playback": "\033[92m",   # green
    "state/app":      "\033[94m",   # blue
    "state/screen":   "\033[96m",   # cyan
    "state/volume":   "\033[93m",   # yellow
    "state/device":   "\033[95m",   # magenta
    "status":         "\033[97m",   # white
    "cmd/":           "\033[91m",   # red (commands coming in)
}
RESET = "\033[0m"
BOLD  = "\033[1m"

def color_for(topic: str) -> str:
    for key, code in TOPIC_COLORS.items():
        if key in topic:
            return code
    return ""

def pretty(payload: str) -> str:
    try:
        obj = json.loads(payload)
        return json.dumps(obj, indent=2)
    except Exception:
        return payload

def on_connect(client, userdata, flags, reason_code, properties=None):
    prefix = userdata["prefix"]
    if reason_code == 0:
        print(f"{BOLD}[monitor] Connected. Subscribing to {prefix}/#...{RESET}\n")
        client.subscribe(f"{prefix}/#")
    else:
        print(f"[monitor] Connection failed: reason={reason_code}")
        sys.exit(1)

def on_message(client, userdata, msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    col = color_for(msg.topic)
    payload = msg.payload.decode("utf-8", errors="replace") if msg.payload else "(empty)"
    print(f"{col}{BOLD}[{ts}] {msg.topic}{RESET}")
    print(pretty(payload))
    print()

def main():
    parser = argparse.ArgumentParser(description="Fire2MQTT MQTT Monitor")
    parser.add_argument("--broker",   default="localhost",     help="MQTT broker host")
    parser.add_argument("--port",     type=int, default=DEFAULT_PORT)
    parser.add_argument("--prefix",   default=DEFAULT_PREFIX,  help="Topic prefix (default: fire2mqtt)")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={"prefix": args.prefix})
    client.on_connect = on_connect
    client.on_message = on_message

    if args.username:
        client.username_pw_set(args.username, args.password)

    print(f"{BOLD}[monitor] Connecting to {args.broker}:{args.port}...{RESET}")
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
