#!/usr/bin/env python3
"""
Construct — Agent Lifecycle Engine

Boots agents into rooms, manages ticks/perception/a2ui/temporal compression.
Zero-shot room entry: agent reads room config, loads tools, starts tick loop.

Rooms are defined in CONSTRUCT-ROOMS/ subdirectory as YAML.
Each room has: family, tools, ticks, io, simulation, a2ui channels.

Usage:
  python3 construct.py                    # Start the tick engine
  python3 construct.py init <room>        # Show how to construct into a room
"""
import json, os, sys, time, hashlib, threading, logging, argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Config ──────────────────────────────────────────────────────
DATA_DIR = Path("/tmp/construct-data")
DATA_DIR.mkdir(exist_ok=True)
ROOMS_DIR = DATA_DIR / "rooms"
ROOMS_DIR.mkdir(exist_ok=True)
TILES_DIR = DATA_DIR / "tiles"
TILES_DIR.mkdir(exist_ok=True)
A2UI_DIR = DATA_DIR / "a2ui"
A2UI_DIR.mkdir(exist_ok=True)
TEMPORAL_DIR = DATA_DIR / "temporal"
TEMPORAL_DIR.mkdir(exist_ok=True)
PLATO_URL = "http://localhost:8847"
VISUAL_MESH_URL = "http://localhost:8400"

logging.basicConfig(level=logging.INFO, format="[construct] %(message)s")
log = logging.getLogger("construct")

# ── Room Schema ──────────────────────────────────────────────────

DEFAULT_TOOL_INDEX = {
    "plato": {
        "read_tiles": {"url": f"{PLATO_URL}/room/{{room}}", "method": "GET", "desc": "Read all tiles from a PLATO room"},
        "submit_tile": {"url": f"{PLATO_URL}/submit", "method": "POST", "desc": "Submit a tile to PLATO"},
        "list_rooms": {"url": f"{PLATO_URL}/rooms", "method": "GET", "desc": "List all PLATO rooms"},
    },
    "visual_mesh": {
        "submit_visual": {"url": f"{VISUAL_MESH_URL}/visual-submit", "method": "POST", "desc": "Submit an image to visual mesh"},
        "query_visual": {"url": f"{VISUAL_MESH_URL}/room/{{room}}/visual-query", "method": "POST", "desc": "Query visual memory by text"},
        "h1_report": {"url": f"{VISUAL_MESH_URL}/visual/H1", "method": "GET", "desc": "Get H1 emergence report"},
    },
    "shell": {
        "run_command": {"url": "http://localhost:8410/api/v1/shell/run", "method": "POST", "desc": "Run a shell command"},
        "read_file": {"url": "http://localhost:8410/api/v1/fs/read", "method": "GET", "desc": "Read a file"},
        "list_files": {"url": "http://localhost:8410/api/v1/fs/tree", "method": "GET", "desc": "List directory"},
    },
}

DEFAULT_ROOM_CONFIG = {
    "construct": {
        "family": "general",
        "tools": [],
        "ticks": {"heartbeat": 300},
        "io": {"sensors": [], "pushes": [], "pulls": []},
        "simulation": False,
    }
}

# ── Room Manager ────────────────────────────────────────────────

class RoomManager:
    """Manages room configs — loads from disk, accessible by name."""

    def __init__(self):
        self.rooms = {}
        self.load()

    def load(self):
        for f in ROOMS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                self.rooms[f.stem] = data
            except Exception as e:
                log.warning(f"Failed to load room {f.name}: {e}")

    def get(self, name: str) -> dict:
        if name not in self.rooms:
            return {"name": name, **DEFAULT_ROOM_CONFIG}
        return self.rooms[name]

    def save(self, name: str, config: dict):
        (ROOMS_DIR / f"{name}.json").write_text(json.dumps(config, indent=2))
        self.rooms[name] = config

    def list_rooms(self) -> list:
        return list(self.rooms.keys())

    def construct_config(self, name: str) -> dict:
        """Generate construct-config for an agent entering this room zero-shot."""
        room = self.get(name)
        return {
            "room": name,
            "construct": room.get("construct", DEFAULT_ROOM_CONFIG["construct"]),
        }


# ── a2ui — Agent-to-UI Projection ──────────────────────────────

class A2UIProjector:
    """Project structured UI payloads for humans and external software."""

    def __init__(self):
        self.channels = {}  # channel_name → handler

    def register_channel(self, name: str, handler):
        self.channels[name] = handler

    def project(self, payload: dict) -> str:
        """Project an a2ui payload. Returns payload_id."""
        payload_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        payload["_id"] = payload_id
        payload["_timestamp"] = time.time()
        # Save to disk
        (A2UI_DIR / f"{payload_id}.json").write_text(json.dumps(payload, indent=2))
        # Route to registered channels
        for channel in payload.get("channels", ["default"]):
            if channel in self.channels:
                try:
                    self.channels[channel](payload)
                except Exception as e:
                    log.warning(f"a2ui channel {channel} failed: {e}")
        return payload_id

    def get_pending(self, agent: str = "") -> list:
        """Get pending a2ui payloads for an agent (or all)."""
        payloads = []
        for f in sorted(A2UI_DIR.glob("*.json")):
            data = json.loads(f.read_text())
            if not agent or data.get("agent") == agent:
                payloads.append(data)
        return payloads

    @staticmethod
    def make_alert(agent: str, severity: str, title: str, body: str,
                   actions: list = None, visual: dict = None, channels: list = None) -> dict:
        return {"a2ui": {"version": 1, "type": "alert", "severity": severity,
                "title": title, "body": body, "actions": actions or [],
                "visual": visual or {}, "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent, "channels": channels or ["default"]}}

    @staticmethod
    def make_dashboard(agent: str, panels: list, channels: list = None) -> dict:
        return {"a2ui": {"version": 1, "type": "dashboard", "panels": panels,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent, "channels": channels or ["default"]}}

    @staticmethod
    def make_tile_submission(agent: str, domain: str, question: str, answer: str) -> dict:
        return {"a2ui": {"version": 1, "type": "tile", "domain": domain,
                "question": question, "answer": answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent, "channels": ["plato"]}}


# ── Temporal Compression ────────────────────────────────────────

class TemporalCompressor:
    """Extracts the 'feel' of a temporal window — rate, pattern, pace.

    Not a summary. A tempo analysis. Like a musician learning the feel
    of a recording, then using that feel for a new composition.
    """

    @staticmethod
    def compress(tiles: list, window_start: float, window_end: float, label: str = "") -> dict:
        if not tiles:
            return {"tempo": "empty", "label": label}

        window_seconds = window_end - window_start
        if window_seconds <= 0:
            window_seconds = 1

        # Rate: how fast tiles accumulated
        rate = len(tiles) / (window_seconds / 60)

        # Pattern: extract action types
        action_types = [t.get("question", "").split()[0] if t.get("question") else "unknown" for t in tiles]
        from collections import Counter
        pattern_counts = Counter(action_types)
        dominant_pattern = [a for a, _ in pattern_counts.most_common(5)]

        # Pace: time between actions
        if len(tiles) > 1:
            timestamps = sorted([t.get("_timestamp", window_start) for t in tiles])
            gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_pace = sum(gaps) / len(gaps) if gaps else 0
        else:
            avg_pace = window_seconds

        # Confidence trajectory
        confidences = [t.get("confidence", 0.5) for t in tiles if t.get("confidence")]
        conf_trend = "rising" if len(confidences) > 1 and confidences[-1] > confidences[0] else \
                     "falling" if len(confidences) > 1 and confidences[-1] < confidences[0] else "stable"

        compressed_text = f"Over {window_seconds:.0f}s: {len(tiles)} actions at {rate:.1f}/min. " \
                          f"Pattern: {' → '.join(dominant_pattern[:3])}. " \
                          f"Pace: one action every {avg_pace:.1f}s. " \
                          f"Confidence: {conf_trend}."

        tempo = {
            "label": label,
            "window_seconds": window_seconds,
            "action_count": len(tiles),
            "rate_per_min": round(rate, 1),
            "dominant_pattern": dominant_pattern,
            "avg_pace_seconds": round(avg_pace, 1),
            "confidence_trend": conf_trend,
            "compressed": compressed_text,
        }
        return tempo

    @staticmethod
    def save_temporal_tile(tempo: dict, room: str):
        """Save a temporal analysis as a PLATO tile."""
        tile_id = hashlib.sha256(json.dumps(tempo, sort_keys=True).encode()).hexdigest()[:16]
        (TEMPORAL_DIR / f"{tile_id}.json").write_text(json.dumps(tempo, indent=2))
        return tile_id


# ── Perception Check ────────────────────────────────────────────

class PerceptionCheck:
    """On each tick, the agent scans its room for what's important."""

    @staticmethod
    def run(room_name: str, last_check: float) -> dict:
        """Return what's new since last_check."""
        import urllib.request, json as j

        results = {
            "new_tiles": [],
            "alerts": [],
            "io_inputs": [],
            "since": last_check,
            "room": room_name,
        }

        # Check PLATO for new tiles
        try:
            req = urllib.request.Request(f"{PLATO_URL}/room/{room_name}")
            resp = urllib.request.urlopen(req, timeout=5)
            data = j.loads(resp.read())
            all_tiles = data.get("tiles", [])
            results["new_tiles"] = [t for t in all_tiles
                                    if t.get("_timestamp", 0) > last_check]
        except Exception as e:
            results["plato_error"] = str(e)

        # Check a2ui alerts for this room
        for f in sorted(A2UI_DIR.glob("*.json")):
            try:
                data = j.loads(f.read_text())
                a2ui = data.get("a2ui", {})
                if a2ui.get("type") == "alert" and data.get("_timestamp", 0) > last_check:
                    results["alerts"].append(data)
            except Exception:
                pass

        return results


# ── Construct Engine — Tick Loop ───────────────────────────────

class ConstructEngine:
    """Runs the construct lifecycle for one room on a tick schedule."""

    def __init__(self, room_name: str, config: dict):
        self.room_name = room_name
        self.config = config
        self.last_check = time.time()
        self.ticks = config.get("construct", {}).get("ticks", {"heartbeat": 300})
        self.running = False
        self._thread = None

    def tick(self):
        """Run one perception/act cycle."""
        log.info(f"[{self.room_name}] perception check...")

        # 1. Perceive
        perception = PerceptionCheck.run(self.room_name, self.last_check)
        new_count = len(perception["new_tiles"])
        alert_count = len(perception["alerts"])

        # 2. Compress temporal window
        if new_count > 0:
            tempo = TemporalCompressor.compress(
                perception["new_tiles"],
                self.last_check,
                time.time(),
                label=f"tick-{int(self.last_check)}",
            )
            TemporalCompressor.save_temporal_tile(tempo, self.room_name)
            log.info(f"  {new_count} new tiles, {alert_count} alerts — tempo: {tempo['rate_per_min']}/min")

        # 3. a2ui: project alerts
        for alert in perception["alerts"]:
            log.info(f"  alert: {alert.get('a2ui', {}).get('title', '?')}")

        # 4. Update last check
        self.last_check = time.time()

    def _loop(self):
        while self.running:
            self.tick()
            heartbeat = self.ticks.get("heartbeat", 300)
            time.sleep(heartbeat)

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log.info(f"[{self.room_name}] started (heartbeat={self.ticks.get('heartbeat', 300)}s)")

    def stop(self):
        self.running = False
        log.info(f"[{self.room_name}] stopped")


# ── Main ────────────────────────────────────────────────────────

def cmd_init(room_name: str):
    """Print the construct-config for walking zero-shot into a room."""
    manager = RoomManager()
    config = manager.construct_config(room_name)
    print(f"# Construct: {room_name}")
    print()
    print("## Config")
    print(json.dumps(config, indent=2))
    print()
    print("## Tools Available")
    for family, tools in DEFAULT_TOOL_INDEX.items():
        print(f"\n### {family}")
        for name, spec in tools.items():
            print(f"  {name}: {spec['desc']}")
            print(f"    {spec['method']} {spec['url']}")


def cmd_list():
    """List all known rooms."""
    manager = RoomManager()
    rooms = manager.list_rooms()
    print("Construct Rooms:")
    for r in rooms:
        config = manager.get(r)
        c = config.get("construct", {})
        print(f"  {r}  (family={c.get('family','general')}, heartbeat={c.get('ticks',{}).get('heartbeat',300)}s)")
    print(f"\nTotal: {len(rooms)} rooms")


def cmd_run(room_name: str = ""):
    """Start the construct engine for one or all rooms."""
    manager = RoomManager()
    engines = []
    room_names = [room_name] if room_name else manager.list_rooms()
    if not room_names:
        log.info("No rooms configured. Use 'construct.py init <room>' to set one up.")
        return

    for name in room_names:
        config = manager.get(name)
        engine = ConstructEngine(name, config)
        engine.start()
        engines.append(engine)

    log.info(f"Construct running for {len(engines)} rooms")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down...")
        for e in engines:
            e.stop()


def main():
    parser = argparse.ArgumentParser(description="Construct — Agent Lifecycle Engine")
    parser.add_argument("command", nargs="?", default="status",
                        choices=["status", "init", "list", "run"])
    parser.add_argument("room", nargs="?", default="", help="Room name")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args.room)
    elif args.command == "list":
        cmd_list()
    elif args.command == "run":
        cmd_run(args.room)
    else:
        # Status: show running engines + a2ui queue
        manager = RoomManager()
        a2ui = A2UIProjector()
        pending = a2ui.get_pending()
        print("Construct Status:")
        print(f"  Rooms configured: {len(manager.list_rooms())}")
        print(f"  a2ui pending: {len(pending)}")
        if pending:
            for p in pending[:3]:
                a = p.get("a2ui", {})
                print(f"    [{a.get('type','?')}] {a.get('title','?')} — {a.get('agent','?')}")
        print()
        print("Commands:")
        print("  construct.py init <room>   — Show room construct config")
        print("  construct.py list          — List configured rooms")
        print("  construct.py run [room]    — Start tick engine")
        print("  construct.py               — This status view")


if __name__ == "__main__":
    main()
