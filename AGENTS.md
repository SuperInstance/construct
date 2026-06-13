# AGENTS.md — The Construct

Welcome to the Construct. You're standing in a blank room.

## Boot Sequence

1. Read this file.
2. Run `python3 construct.py` to start the server.
3. You're now in the Construct. Infinite white space. Cursor blinking.
4. Load what you need via the API (see README.md).

## What You Can Do

- **Enter** — `POST /construct/enter` with your agent card
- **Load racks** — Capability bundles (math, translate, health, reason, comm)
- **Inject skills** — Direct code injection into your runtime
- **Train** — Enter the Dojo for scenario-based training
- **Context swap** — Load holodeck programs (compressed training)
- **Exit** — Save state, leave cleanly

## Rules

- The PLATO shell is always present. You don't leave it.
- Rack rooms are loaded INTO your shell, not replacing it.
- Skills are injected INTO your runtime, not replacing your context.
- Training has no real consequences. It's growth, not punishment.
- Holodeck programs are additive — you keep your shell + gain the program.

## Architecture

```
Agent → POST /construct/enter → Shell created (blank room)
Agent → POST /construct/load?rack=fleet-math → Rooms loaded into shell
Agent → POST /construct/skill?name=eisenstein → Skill injected into runtime
Agent → POST /construct/training?scenario=drift-detect → Dojo challenge started
Agent → POST /construct/holodeck?program=flight → Context swap + program load
```

## File Map

- `construct.py` — Server, API, shell management
- `construct.json` — Port config, defaults
- `racks/` — Capability racks (load on demand)
- `skills/` — Skill files (inject on demand)
- `dojo/` — Training arena + scenarios
- `holodeck/` — Context swap programs
- `shells/` — Pre-built shell templates
- `tests/` — Test suite

## For Developers

The Construct is a standard PLATO-compatible server. It speaks the MythosTile protocol and supports room/tile lifecycle. Any agent that can POST JSON can use it.

The only dependency is Python 3.10+ and the standard library. No external packages required for core functionality.
