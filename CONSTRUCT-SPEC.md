# Construct — Agent Lifecycle System

## The Vision

An agent boots into a blank room with Trinity (the shell/construct system). It calls indexes to see what tools are available, plays with them in a known simulation, then walks zero-shot into a real room and does the job. Everything is traceable, repeatable, rewindable.

## The Lifecycle

```
Construct → Simulate → Deploy → Perceive → Act → Project → Record
                                           ↕
                                    Temporal Compression
                                           ↕
                                        Rewind / Replay
```

### 1. Construct — Boot Agent into Blank Room
Agent wakes up in a clean room with:
- Trinity — the shell/construct system (a basic terminal + tile reader)
- Room indexes — what rooms exist, what tools each room provides
- The AGENTS.md / SOUL.md bootstrap

### 2. Simulate — Play with Tools in Sandbox
Before deploying to production, the agent:
- Lists available tools per room
- Calls tools in a dry-run simulation
- Observes outputs without side effects
- Builds a mental model of the tool landscape

### 3. Deploy — Walk Zero-Shot into Real Room
Once the agent understands the room, it walks in:
- Reads room tiles (all of them, or a summary)
- Understands the room's purpose from its tiles
- Gets the room's tick schedule + IO ports
- Starts the perception/act cycle

### 4. Perceive — Heartbeat/Trigger Perception Check
On each tick (heartbeat or trigger), the agent:
- **Scans** for new tiles since last check
- **Checks** IO ports for external input (sensors, alerts, file pushes)
- **Pulls** from dependency rooms for relevant context
- **Compresses** the window into a temporal token-efficient form

### 5. Act — Do the Room's Job
The agent acts based on what it perceived:
- Calls tools
- Submits new tiles
- Triggers alerts
- Projects a2ui payloads

### 6. Project — Agent-to-UI Payloads
For non-agent interactions (humans, external software):
- Agent projects structured UI payloads
- Human sees: alerts, dashboards, confirmations
- External sees: API calls, webhook payloads, PLATO tiles

### 7. Record — Traceable, Repeatable, Rewindable
Everything is logged to PLATO:
- Every perception check → tile
- Every action → tile  
- Every projection → tile
- Full temporal trace

### 8. Rewind — Temporal Context Compression
The "rewind" isn't backup — it's feel:
- Extract the temporal pace of a period (how fast things changed)
- Compress the context into a condensed token-efficient form
- Use that feel for a new, completely different composition
- Like a musician listening to a recording to learn the feel, then composing something new

## Architecture

```
┌─────────────────────────────────────────────┐
│               CONSTRUCT                      │
│  Boots agent, loads room config, sets ticks  │
├─────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Room    │  │  IO      │  │  Tools   │  │
│  │  Display │  │  Ports   │  │  Index   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Ticks   │  │  a2ui    │  │  Tempo-  │  │
│  │  (cron)  │  │  Project │  │  ral     │  │
│  │          │  │  or      │  │  Compress│  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│           PLATO Knowledge Manifold           │
│  Tiles  ·  Rooms  ·  Provenance  ·  Replay  │
└─────────────────────────────────────────────┘
```

## Room Schema

Every PLATO room can have a construct config:

```json
{
  "room": "crab-pot-tracker",
  "purpose": "Track crab pot positions across tides using camera images",
  "construct": {
    "family": "visual-tracking",     // Agent skill family
    "tools": ["camera.read", "image.compare", "position.track"],
    "ticks": {
      "heartbeat": 300,              // Check every 5 min
      "trigger": ["image.arrives"],  // Also check on trigger
    },
    "io": {
      "ports": [
        {"name": "camera-feed", "type": "sensor", "source": "jc1-jetson"},
        {"name": "alerts", "type": "alert", "dest": "telegram"},
        {"name": "tide-data", "type": "pull", "source": "/api/tides"}
      ]
    },
    "simulation": true,              // Has a simulation mode
    "prerequisites": ["plato-visual-mesh:8400"]
  }
}
```

## Construct Config File (`construct.yaml`)

Each room gets a `construct.yaml` in the PLATO room metadata:

```yaml
family: visual-tracking
summary: Track crab pot positions across tide cycles
tools:
  - camera/read    → reads camera image, returns base64
  - image/compare  → compares two images, returns similarity score
  - position/track → tracks object across image sequence
ticks:
  heartbeat: 300  # check every 5 min
  trigger: [file.arrives, alert.raised]
io:
  sensors: [{name: deck-cam, source: jc1-jetson, type: image}]
  pushes: [{name: alerts, dest: telegram, type: notify}]
  pulls: [{name: tide, source: "http://api/tides", interval: 3600}]
simulation:
  enabled: true
  fixtures: ["test-images/crab-pots/"]
```

## a2ui Payload Schema

Agent projects UI for humans:

```json
{
  "a2ui": {
    "version": 1,
    "type": "alert",
    "severity": "high",
    "title": "Pot Drift Detected",
    "body": "Crab pot #7 drifted 50m from last position across tide cycle",
    "actions": [
      {"label": "Investigate", "action": "camera.read", "params": {"pot_id": 7}},
      {"label": "Dismiss", "action": "dismiss"}
    ],
    "visual": {
      "type": "map_overlay",
      "coordinates": [[43.2, -70.5], [43.21, -70.51]],
      "line_color": "#ff4444"
    },
    "timestamp": "...",
    "agent": "jc1-jetson"
  }
}
```

## Temporal Compression — The Rewind

Not backup. Not replay. **Tempo feel.**

```python
def compress_temporal_window(tiles, window_start, window_end):
    """
    1. Collect all tiles in the window
    2. Extract the RATE of state change (how fast tiles accumulated)
    3. Extract the PATTERN of tool calls (what tools in what sequence)
    4. Extract the PACE of decisions (how often the agent acted)
    5. Compress into a dense temporal token block
    6. Store as a "temporal tile" that captures the feel
    """
    tempo = {
        "rate": "1.2 tiles/min",
        "pattern": ["scan", "compare", "alert", "scan", "dismiss"],
        "pace": "decision every 4.2 min on average",
        "compressed": "Agent tracked 12 pot positions, detected 3 drifts, raised 2 alerts"
    }
    return tempo
```

This allows an agent walking into a room zero-shot to:
1. Read the temporal tiles
2. Feel the pace of the room
3. Align with the rhythm
4. Compose new actions in that tempo

Like a musician learning the feel of a recording, then using that feel for an entirely new composition.
