# 🌀 Construct — Agent Lifecycle Engine

Boot agents into blank rooms. Manages ticks, perception, a2ui projection, temporal compression.

## Quick Start
```bash
# Requires: PLATO (:8847) running (core fleet service)
# Requires: Python 3.10+
# Clone and install
git clone https://github.com/SuperInstance/construct.git
cd construct
bash install.sh

# Or run directly
python3 construct.py                  # Status
python3 construct.py init <room>      # Show room construct config
python3 construct.py list             # List configured rooms
python3 construct.py run [room]       # Start tick engine
```

## Dependencies
- **PLATO** (:8847) — Required for tile storage (always running in fleet)
- **python3** — Standard library only (no pip deps for core)

## Concepts
| Concept | What It Does |
|---------|-------------|
| Construct | Agent wakes up in blank room with Trinity (shell) |
| Room Display | What each room shows + its tick schedule |
| Perception Check | On each tick, scan for new tiles, alerts, IO |
| a2ui Payload | Agent projects structured UI for humans/external |
| Temporal Compression | Extracts the "feel" of a time window — rate, pattern, pace |

## Rooms
Rooms live in `construct-data/rooms/` as JSON. Each room has:
```json
{"name": "crab-tracker", "construct": {
  "family": "visual-tracking",
  "tools": ["plato.read_tiles", "image.compare"],
  "ticks": {"heartbeat": 300},
  "io": {"sensors": [], "pushes": [], "pulls": []}
}}
```
