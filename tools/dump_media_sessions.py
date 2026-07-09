#!/usr/bin/env python3
"""Watch ALL concurrent MediaSessions on a live Fire TV via ADB, and show which one the
Fire2MQTT APK's ``selectPrimary`` logic would report.

Unlike ``dump_rules_from_adb.py`` (single package, ``state=`` only), this dumps every session in
the stack — package, active flag, PlaybackState int, position, and metadata/title — on each change,
with millisecond timestamps. It also computes the session the APK would pick
(``maxByOrNull(statePriority)``, first-at-max), so you can see phantom ad/pre-roll sessions
outranking or swapping with the real content session (the Prime Video flapping bug).

Usage:
    python3 tools/dump_media_sessions.py --device-ip 10.10.10.115:5555 --interval 0.25
    python3 tools/dump_media_sessions.py --device-ip 10.10.10.115:5555 --filter amazon
"""
from __future__ import annotations

import argparse
import re
import subprocess
import time
from dataclasses import dataclass

# Mirrors android.media.session.PlaybackState.STATE_* (same map as dump_rules_from_adb.py).
STATE_NAMES = {
    None: "no-state",
    0: "NONE",
    1: "STOPPED",
    2: "PAUSED",
    3: "PLAYING",
    4: "FAST_FORWARDING",
    5: "REWINDING",
    6: "BUFFERING",
    7: "ERROR",
    8: "CONNECTING",
    9: "SKIP_PREVIOUS",
    10: "SKIP_NEXT",
    11: "SKIP_QUEUE_ITEM",
}


def _state_priority(state: int | None) -> int:
    """Exactly the APK's MediaSessionWatcher.statePriority (current behaviour)."""
    if state in (3, 6, 4, 5):  # PLAYING, BUFFERING, FAST_FORWARDING, REWINDING
        return 3
    if state == 2:  # PAUSED
        return 2
    if state == 1:  # STOPPED
        return 1
    return 0


@dataclass
class Session:
    package: str
    active: bool
    state: int | None
    position: int | None
    metadata: str

    def key(self) -> tuple:
        # Ignore position for change-detection: a running position isn't "flapping".
        return (self.package, self.active, self.state, self.metadata)


def run_adb(device_ip: str, command: str) -> str:
    result = subprocess.run(
        ["adb", "-s", device_ip, "shell", *command.split()],
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_sessions(raw: str) -> list[Session]:
    """Parse the 'Sessions Stack' region of `dumpsys media_session` into ordered Session rows.

    The stack preserves priority order. Each session block is a 4-space-indented header line
    ('... (userId=N)') followed by 6-space-indented fields (package=, active=, state=, metadata:).
    """
    lines = raw.splitlines()
    # Bound the parse to the session stack so we don't pick up the 'Audio playback' tail.
    try:
        start = next(i for i, ln in enumerate(lines) if "Sessions Stack" in ln)
    except StopIteration:
        return []
    end = next(
        (i for i, ln in enumerate(lines[start + 1 :], start + 1) if "Audio playback" in ln),
        len(lines),
    )

    header_re = re.compile(r"^ {4}\S.*\(userId=\d+\)\s*$")
    sessions: list[Session] = []
    block: list[str] = []

    def flush() -> None:
        if not block:
            return
        text = "\n".join(block)
        pkg = _find(r"package=(\S+)", text) or "?"
        active = (_find(r"active=(true|false)", text) or "false") == "true"
        state_m = re.search(r"state=PlaybackState \{state=(\d+), position=(-?\d+)", text)
        state = int(state_m.group(1)) if state_m else None
        position = int(state_m.group(2)) if state_m else None
        meta = "none" if re.search(r"metadata: null", text) else _find(r"metadata: (.+)", text) or "?"
        sessions.append(Session(pkg, active, state, position, meta))

    for ln in lines[start + 1 : end]:
        if header_re.match(ln):
            flush()
            block = [ln]
        elif block:
            block.append(ln)
    flush()
    return sessions


def _find(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def select_primary(sessions: list[Session]) -> Session | None:
    """Replicate the APK's selectPrimary: maxByOrNull(statePriority), first-at-max (list order)."""
    if not sessions:
        return None
    best = sessions[0]
    for s in sessions[1:]:
        if _state_priority(s.state) > _state_priority(best.state):
            best = s
    return best


def _fmt(s: Session, *, primary: bool) -> str:
    marker = ">>" if primary else "  "
    name = STATE_NAMES.get(s.state, f"S{s.state}")
    act = "active" if s.active else "  idle"
    meta = (s.metadata[:40] + "…") if len(s.metadata) > 41 else s.metadata
    return f"  {marker} {act} pri={_state_priority(s.state)} {name:<9} pos={s.position} {s.package}  [{meta}]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-ip", required=True, dest="device_ip", help="host:port for adb -s")
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--filter", default="", help="only show sessions whose package contains this")
    args = parser.parse_args()

    print(f"Watching all media sessions on {args.device_ip} (interval {args.interval}s)")
    print("Reproduce: open Prime Video → open a series → press play. Ctrl+C to stop.")
    print(">> marks the session the APK's selectPrimary would report.\n")

    last_key: tuple | None = None
    try:
        while True:
            raw = run_adb(args.device_ip, "dumpsys media_session")
            sessions = parse_sessions(raw)
            if args.filter:
                sessions = [s for s in sessions if args.filter in s.package]
            primary = select_primary(sessions)
            # Change key: every session's (pkg,active,state,meta) + which one is primary.
            key = (tuple(s.key() for s in sessions), primary.package if primary else None,
                   primary.state if primary else None)
            if key != last_key:
                ts = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
                picked = (
                    f"{STATE_NAMES.get(primary.state)} {primary.package}" if primary else "none"
                )
                print(f"[{ts}] {len(sessions)} sessions | APK reports: {picked}")
                for s in sessions:
                    print(_fmt(s, primary=s is primary))
                print()
                last_key = key
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDone.")


if __name__ == "__main__":
    main()
