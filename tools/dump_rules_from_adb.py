#!/usr/bin/env python3
"""Harvest media_session_state values from a live Fire TV Stick via ADB.

Run this while interacting with an app (play, pause, stop) to observe
the raw MediaSession states. Use the output to build entries for data/rules.py.

Usage:
    python3 tools/dump_rules_from_adb.py --device-ip 192.168.1.50 --package com.netflix.ninja
"""
import argparse
import subprocess
import re
import time


def run_adb(device_ip: str, command: str) -> str:
    result = subprocess.run(
        ["adb", "-s", device_ip, "shell"] + command.split(),
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_media_session_state(device_ip: str, package: str) -> int | None:
    raw = run_adb(device_ip, "dumpsys media_session")
    # Find the block for the target package
    sections = raw.split("Session #")
    for section in sections:
        if package in section:
            match = re.search(r"state=PlaybackState \{state=(\d+)", section)
            if match:
                return int(match.group(1))
    return None


def main():
    parser = argparse.ArgumentParser(description="Dump MediaSession states via ADB")
    parser.add_argument("--device-ip", required=True, dest="device_ip")
    parser.add_argument("--package", required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    print(f"Watching {args.package} on {args.device_ip}")
    print(f"Interact with the app (play, pause, stop). Press Ctrl+C to stop.\n")
    print(f"{'Time':12} | {'State int':10} | Description")
    print("-" * 40)

    STATE_NAMES = {
        None: "no session",
        0: "STATE_NONE",
        1: "STATE_STOPPED",
        2: "STATE_PAUSED",
        3: "STATE_PLAYING",
        4: "STATE_FAST_FORWARDING",
        5: "STATE_REWINDING",
        6: "STATE_BUFFERING",
        7: "STATE_ERROR",
        8: "STATE_CONNECTING",
        9: "STATE_SKIPPING_TO_PREVIOUS",
        10: "STATE_SKIPPING_TO_NEXT",
        11: "STATE_SKIPPING_TO_QUEUE_ITEM",
    }

    last_state = "INIT"
    try:
        while True:
            state = get_media_session_state(args.device_ip, args.package)
            if state != last_state:
                ts = time.strftime("%H:%M:%S")
                name = STATE_NAMES.get(state, f"STATE_{state}")
                print(f"{ts:12} | {str(state):10} | {name}")
                last_state = state
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDone.")


if __name__ == "__main__":
    main()
