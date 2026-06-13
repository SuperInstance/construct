# The Construct: Architecture Specification

**Version:** 1.0.0-rc  
**Status:** Technical Review  
**Classification:** Internal Engineering

---

## 1. System Overview

### 1.1 What the Construct Is

The Construct is a blank PLATO shell — a bootable, stateful execution environment that any AI agent can inhabit. It is not a framework, not a scaffolding library, and not a prompt template. It is a running server with persistent state, a tile-addressable memory surface, and a docking protocol that standardizes how agents enter, operate within, and exit a shared cognitive workspace.

PLATO (Persistent Layer Architecture for Tiled Objects) treats cognition as a spatial medium: memory is tiled, tiles are versioned, and the workspace evolves under conservation constraints. The Construct instantiates a PLATO room that begins empty — no pre-loaded facts, no baked-in persona — and provides the loading infrastructure that agents use to mount racks (domain knowledge), inject skills (callable behaviors), and enter training scenarios or holodeck programs.

A PLATO shell is to an AI agent what a container runtime is to a process: it provides the execution boundary, the filesystem metaphor, the resource accounting, and the lifecycle hooks. The Construct is the minimal viable shell — 900 lines, 42 tests, no dead weight.

### 1.2 What the Construct Is For

The Construct solves a specific problem: agents trained or fine-tuned in isolation have no standard way to share a workspace, coordinate on state, or demonstrate that their outputs satisfy conservation invariants. The Construct provides:

- **A blank slate for agent instantiation** — boot any agent into a known-good empty state without prior contamination
- **Rack-based domain loading** — mount fleet-math, fleet-translate, fleet-health, fleet-reason, or fleet-comm as structured tile bundles
- **Skill injection** — bind callable behaviors (eisenstein, hebbian, conservation, translation, fault-detect) to the shell's dispatch table
- **Training infrastructure** — run agents through dojo scenarios against adversarial, drift, conservation, and translation challenges
- **Holodeck context swap** — hot-swap the agent's operational context (flight, combat, medical, engineering) without rebooting
- **Conservation enforcement** — reject tile writes that would violate γ+H = C − α·ln V

The primary user of the Construct is any AI agent that needs a verified, auditable execution environment with persistent tile state and fleet coordination.

### 1.3 Conservation Law as Deployment Constraint

The conservation law governs all persistent state in the system:

```
γ + H = C − α·ln V
```

Where:
- `γ` — geometric distortion (tile layout deformation under semantic load)
- `H` — Hebbian weight entropy (sum of connection weight entropies across active synapses)
- `C` — conserved constant for the shell instance (set at boot, immutable during session)
- `α` — annealing coefficient (controls cooling rate under load)
- `V` — tile volume (count of active tiles in the working surface)

Any write to the tile surface that would violate this equation is rejected by the WAL before commit. Shells operating under heavy rack load will see increasing `V`, which reduces the right-hand side budget; the system compensates by increasing geometric regularization pressure or scheduling Hebbian weight pruning. Deployment operators must provision sufficient headroom in `C` for their expected rack combination.

### 1.4 Calibration Principle as Security Principle

The calibration principle — *never calibrate from your own instrument* — governs all cross-agent validation in the Construct. No agent may be the sole verifier of its own tile writes. Every tile that enters the persistent WAL must pass through at least one external verifier (content verifier, cross-validation peer, or canary comparison). This applies to skill injection (a skill cannot attest its own correctness), rack loading (a rack bundle cannot self-certify provenance), and holodeck program activation (the program cannot validate its own context swap). External validation chains are mandatory; circular validation graphs are rejected at the fleet router.

---

## 2. Component Architecture

### 2.1 Top-Level Component Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                          THE CONSTRUCT                              │
│                                                                     │
│  ┌───────────────┐    ┌───────────────┐    ┌────────────────────┐  │
│  │ construct.py  │    │  Rack Loader  │    │  Skill Injector    │  │
│  │ (shell server)│◄──►│ (5 rack types)│    │ (5 skill types)    │  │
│  └──────┬────────┘    └───────┬───────┘    └─────────┬──────────┘  │
│         │                    │                       │             │
│         ▼                    ▼                       ▼             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PLATO Room Server                        │   │
│  │           (WAL + Tile Lifecycle + Room State)               │   │
│  └──────────────┬──────────────────────────┬───────────────────┘   │
│                 │                          │                       │
│         ┌───────▼────────┐    ┌────────────▼──────────┐           │
│         │  Dojo Arena    │    │  Holodeck Controller  │           │
│         │ (4 scenarios)  │    │  (4 programs)         │           │
│         └───────┬────────┘    └────────────┬──────────┘           │
│                 │                          │                       │
└─────────────────┼──────────────────────────┼───────────────────────┘
                  │                          │
        ┌─────────▼──────────────────────────▼──────────┐
        │              PLATFORM SERVICES                 │
        │                                                │
        │  ┌─────────────┐  ┌──────────────────────┐    │
        │  │  Hebbian    │  │   Fleet Router       │    │
        │  │  Service    │  │ (self-healing+domain) │    │
        │  └──────┬──────┘  └──────────┬───────────┘    │
        │         │                    │                 │
        │  ┌──────▼──────┐  ┌──────────▼───────────┐    │
        │  │  Content    │  │  GL(9) Fault Detect  │    │
        │  │  Verifier   │  │  (semantic fault)    │    │
        │  └─────────────┘  └──────────────────────┘    │
        │                                                │
        │  ┌──────────────────────────────────────────┐  │
        │  │         Cashew Bridge                    │  │
        │  │  (bidirectional docking, memory systems) │  │
        │  └──────────────────────────────────────────┘  │
        └────────────────────────────────────────────────┘
```

### 2.2 Data Flow: Agent Boot Sequence

```
Agent Process
     │
     │  POST /shell/boot {template, agent_id, rack_list, skill_list}
     ▼
construct.py
     │
     ├──► validate agent_id (fleet router auth)
     │
     ├──► select shell template (blank/forklift/sprinter/service)
     │
     ├──► allocate room (PLATO room server)
     │         └── assigns room_id, sets C constant, opens WAL
     │
     ├──► load racks (rack loader)
     │         └── for each rack: fetch bundle, verify provenance,
     │             write tiles to WAL, update V, check γ+H = C−α·ln V
     │
     ├──► inject skills (skill injector)
     │         └── for each skill: load bytecode, external-verify,
     │             bind to dispatch table, register with Hebbian service
     │
     └──► return ShellHandle {shell_id, room_id, tile_surface_url, ws_endpoint}
```

### 2.3 Data Flow: Tile Write with Conservation Check

```
Agent
  │
  │  PATCH /tile/{tile_id}  {content, semantic_vector}
  ▼
Shell Server
  │
  ├──► GL(9) fault check (semantic vector projection onto fault manifold)
  │         ├── PASS → continue
  │         └── FAIL → 422 SemanticFault, log to WAL
  │
  ├──► compute proposed state: V' = V+1 if new tile
  │                            γ' = recompute geometric distortion
  │                            H' = Hebbian service query (updated entropy)
  │
  ├──► conservation check: γ' + H' ≤ C − α·ln V'
  │         ├── PASS → continue
  │         └── FAIL → 409 ConservationViolation {budget_remaining, suggestion}
  │
  ├──► content verifier (canary + cross-validation)
  │         └── calibration principle: external verifier only, no self-attest
  │
  ├──► WAL commit (append-only, tile_id + version + hash)
  │
  └──► broadcast to subscribed agents via WebSocket
```

---

## 3. API Specification

All endpoints return `application/json`. Error responses follow RFC 9110 Problem Details (`application/problem+json`).

### 3.1 Shell Lifecycle

#### `POST /shell/boot`

Boot a new shell from a template.

**Request:**
```json
{
  "agent_id": "string (required)",
  "template": "blank | forklift | sprinter | service",
  "rack_list": ["fleet-math", "fleet-translate", "fleet-health", "fleet-reason", "fleet-comm"],
  "skill_list": ["eisenstein", "hebbian", "conservation", "translation", "fault-detect"],
  "conservation_budget": 1000.0,
  "annealing_coefficient": 0.1,
  "session_ttl_seconds": 3600
}
```

**Response `201`:**
```json
{
  "shell_id": "uuid",
  "room_id": "uuid",
  "agent_id": "string",
  "template": "blank",
  "conservation_constant": 1000.0,
  "tile_surface_url": "/shell/{shell_id}/tiles",
  "ws_endpoint": "ws://host/shell/{shell_id}/stream",
  "booted_at": "ISO8601",
  "rack_status": {"fleet-math": "loaded", "fleet-translate": "pending"},
  "skill_status": {"eisenstein": "bound", "hebbian": "bound"}
}
```

**Error `409`:** ConservationViolation — requested rack combination exceeds budget C.  
**Error `403`:** AgentNotAuthorized — agent_id not recognized by fleet router.

---

#### `DELETE /shell/{shell_id}`

Graceful shutdown. Flushes WAL, archives tile surface, releases room.

**Response `200`:**
```json
{
  "shell_id": "uuid",
  "tiles_archived": 142,
  "final_conservation_state": {"gamma": 0.43, "H": 7.21, "C": 1000.0, "V": 142},
  "archived_at": "ISO8601"
}
```

---

#### `GET /shell/{shell_id}/status`

**Response `200`:**
```json
{
  "shell_id": "uuid",
  "agent_id": "string",
  "state": "running | suspended | draining | error",
  "conservation": {"gamma": 0.43, "H": 7.21, "C": 1000.0, "alpha": 0.1, "V": 142, "budget_remaining": 212.3},
  "loaded_racks": ["fleet-math"],
  "bound_skills": ["eisenstein", "hebbian"],
  "active_program": null,
  "active_scenario": null,
  "uptime_seconds": 430
}
```

---

### 3.2 Rack Management

#### `POST /shell/{shell_id}/rack/load`

**Request:**
```json
{"rack_name": "fleet-math | fleet-translate | fleet-health | fleet-reason | fleet-comm"}
```

**Response `200`:**
```json
{
  "rack_name": "fleet-math",
  "tiles_loaded": 47,
  "provenance_hash": "sha256:...",
  "verifier_attestation": {"verifier_id": "cv-01", "signed_at": "ISO8601"},
  "conservation_delta": {"V_before": 95, "V_after": 142, "budget_consumed": 48.7}
}
```

**Error `409`:** ConservationViolation — rack load would exceed remaining budget.  
**Error `403`:** ProvenanceFailed — calibration principle: self-attestation rejected.

---

#### `DELETE /shell/{shell_id}/rack/{rack_name}`

Unload rack, reclaim tile slots, update conservation state.

---

#### `GET /shell/{shell_id}/racks`

List all racks with load status and tile counts.

---

### 3.3 Skill Injection

#### `POST /shell/{shell_id}/skill/inject`

**Request:**
```json
{
  "skill_name": "eisenstein | hebbian | conservation | translation | fault-detect",
  "verifier_id": "string (external verifier, calibration principle)",
  "config": {}
}
```

**Response `200`:**
```json
{
  "skill_name": "eisenstein",
  "dispatch_key": "string",
  "hebbian_node_id": "uuid",
  "bound_at": "ISO8601",
  "external_verification": {"verifier_id": "cv-02", "passed": true}
}
```

---

#### `POST /shell/{shell_id}/skill/{skill_name}/invoke`

Invoke a bound skill within the shell context.

**Request:**
```json
{"input": {}, "context_tiles": ["tile_id_1", "tile_id_2"]}
```

**Response `200`:**
```json
{
  "skill_name": "eisenstein",
  "output": {},
  "tiles_modified": ["tile_id_3"],
  "conservation_delta": {},
  "invocation_id": "uuid",
  "latency_ms": 12
}
```

---

### 3.4 Dojo Training Arena

#### `POST /shell/{shell_id}/dojo/start`

**Request:**
```json
{
  "scenario": "drift-detect | adversarial | conservation | translate",
  "difficulty": 1,
  "seed": 42,
  "max_rounds": 20
}
```

**Response `200`:**
```json
{
  "session_id": "uuid",
  "scenario": "drift-detect",
  "initial_state": {},
  "objective": "string",
  "scoring_rubric": {}
}
```

---

#### `POST /shell/{shell_id}/dojo/{session_id}/step`

Submit agent action; receive scenario feedback.

**Request:**
```json
{"action": {}, "reasoning": "string"}
```

**Response `200`:**
```json
{
  "round": 3,
  "feedback": {},
  "score_delta": 0.12,
  "scenario_state": "running | passed | failed | timeout",
  "conservation_impact": {}
}
```

---

### 3.5 Holodeck Context Swap

#### `POST /shell/{shell_id}/holodeck/load`

**Request:**
```json
{
  "program": "flight | combat | medical | engineering",
  "swap_mode": "hot | cold",
  "preserve_tiles": ["tile_id_1"]
}
```

Hot swap replaces context tiles without shell reboot. Cold swap triggers a drain-and-reload cycle.

**Response `200`:**
```json
{
  "program": "flight",
  "swap_mode": "hot",
  "tiles_replaced": 23,
  "tiles_preserved": 1,
  "context_loaded_at": "ISO8601",
  "conservation_recheck": {"passed": true}
}
```

**Error `409`:** swap would violate conservation; use cold swap with higher budget.

---

### 3.6 Tile Surface

#### `GET /shell/{shell_id}/tiles`

Paginated tile listing.

**Query params:** `cursor`, `limit` (max 500), `rack_filter`, `modified_after`

#### `PATCH /tile/{tile_id}`

Write or update a tile. Full conservation + GL(9) + content verification pipeline runs synchronously.

#### `GET /tile/{tile_id}/history`

Full WAL history for a tile: all versions, hashes, verifier attestations.

---

## 4. Data Model

### 4.1 Shell

```python
@dataclass
class Shell:
    shell_id: UUID
    agent_id: str
    template: Literal["blank", "forklift", "sprinter", "service"]
    room_id: UUID
    state: Literal["booting", "running", "suspended", "draining", "error", "archived"]
    
    # Conservation state
    C: float          # conserved constant, set at boot, immutable
    alpha: float      # annealing coefficient
    gamma: float      # geometric distortion (recomputed on every tile write)
    H: float          # Hebbian entropy (queried from Hebbian service)
    V: int            # tile volume (count of active tiles)
    
    # Loaded components
    loaded_racks: List[str]
    bound_skills: Dict[str, SkillHandle]
    active_program: Optional[str]
    active_scenario: Optional[str]
    
    # Lifecycle
    booted_at: datetime
    last_activity: datetime
    session_ttl: int
```

### 4.2 Tile

```python
@dataclass
class Tile:
    tile_id: UUID
    shell_id: UUID
    rack_origin: Optional[str]      # which rack loaded this tile, if any
    skill_origin: Optional[str]     # which skill wrote this tile, if any
    
    content: bytes                  # raw tile content (JSON, binary, or text)
    content_hash: str               # sha256 of content
    semantic_vector: List[float]    # GL(9) embedding (9-dimensional)
    
    version: int                    # monotonic, per tile_id
    created_at: datetime
    modified_at: datetime
    
    # Provenance (calibration principle: must have external attestation)
    verifier_id: str
    verifier_signature: str
    self_attested: bool             # MUST be False for WAL commit
    
    # Conservation bookkeeping
    geometric_weight: float         # contribution to γ
    hebbian_links: List[UUID]       # other tile_ids linked in Hebbian graph
    
    # Lifecycle
    state: Literal["active", "evicted", "archived"]
    eviction_reason: Optional[str]
```

### 4.3 Rack Bundle

```python
@dataclass
class RackBundle:
    rack_name: str
    rack_version: str
    tiles: List[Tile]
    tile_count: int
    provenance_hash: str            # hash of full bundle content
    
    # Calibration principle: external-only attestation
    attestor_id: str                # must differ from rack publisher
    attestation_signature: str
    
    # Conservation metadata
    expected_V_delta: int           # how many tiles this rack adds
    expected_budget_cost: float     # estimated conservation budget consumed
    compatible_templates: List[str]
```

### 4.4 Skill Handle

```python
@dataclass
class SkillHandle:
    skill_name: str
    dispatch_key: str
    bytecode_hash: str
    
    # Hebbian registration
    hebbian_node_id: UUID
    hebbian_weight: float
    
    # Calibration principle: skill cannot self-certify
    external_verifier_id: str
    verification_timestamp: datetime
    
    # Invocation telemetry
    invocation_count: int
    last_invoked: Optional[datetime]
    avg_latency_ms: float
    conservation_budget_consumed: float
```

### 4.5 Dojo Session

```python
@dataclass
class DojoSession:
    session_id: UUID
    shell_id: UUID
    scenario: Literal["drift-detect", "adversarial", "conservation", "translate"]
    difficulty: int                 # 1–5
    seed: int
    
    state: Literal["running", "passed", "failed", "timeout"]
    current_round: int
    max_rounds: int
    
    score: float
    score_history: List[float]
    
    # Conservation tracking across rounds
    conservation_snapshots: List[Dict]
    
    started_at: datetime
    completed_at: Optional[datetime]
```

### 4.6 Holodeck Program

```python
@dataclass
class HolodeckProgram:
    program_name: Literal["flight", "combat", "medical", "engineering"]
    context_tiles: List[Tile]
    tile_count: int
    
    # Hot swap metadata
    swap_mode: Literal["hot", "cold"]
    preserve_tile_ids: List[UUID]
    
    # Conservation pre-check
    expected_V_after_swap: int
    conservation_feasible: bool
    
    loaded_at: Optional[datetime]
```

---

## 5. Deployment

### 5.1 Single-Node (ZeroClaw)

The minimal deployment runs all services in a single process with in-process message passing. Suitable for single-agent development, dojo training, and offline research.

```
┌────────────────────────────────────────────┐
│              Single Node                   │
│                                            │
│  construct.py (uvicorn, port 8400)         │
│  plato_room.py (in-process)                │
│  hebbian_service.py (in-process)           │
│  fleet_router.py (in-process)              │
│  content_verifier.py (in-process)          │
│  cashew_bridge.py (optional)               │
│                                            │
│  SQLite WAL: /data/construct.db            │
│  Rack store: /data/racks/                  │
│  Skill store: /data/skills/                │
└────────────────────────────────────────────┘
```

Resource floor: 512 MB RAM, 2 vCPU, 10 GB disk. Conservation budget ceiling with 5 racks loaded simultaneously: ~800 tiles, C ≈ 2000 recommended.

### 5.2 Multi-Node (Fleet Deployment)

Services split across nodes with the fleet router as the coordination boundary. Each shell is pinned to one PLATO room server; skills and racks are served from a shared object store.

```
                    ┌──────────────────┐
                    │   Fleet Router   │
                    │  (port 8300)     │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
    │  Shell Node  │ │  Shell Node  │ │  Shell Node  │
    │  (8400-8402) │ │  (8400-8402) │ │  (8400-8402) │
    └───────┬──────┘ └───────┬──────┘ └──────┬───────┘
            └────────────────┼────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
    │  Hebbian Svc │ │Content Verify│ │ GL(9) Detect │
    │  (8500)      │ │  (8600)      │ │  (8700)      │
    └──────────────┘ └──────────────┘ └──────────────┘
                             │
                    ┌────────▼──────────┐
                    │  Cashew Bridge    │
                    │  (8800)           │
                    └───────────────────┘
```

### 5.3 Container Deployment

Each service ships as a minimal OCI image. The compose stack:

```yaml
services:
  construct:
    image: openclaw/construct:1.0.0
    ports: ["8400:8400"]
    environment:
      PLATO_ROOM_URL: http://plato:8100
      HEBBIAN_URL: http://hebbian:8500
      FLEET_ROUTER_URL: http://router:8300
      CONTENT_VERIFIER_URL: http://verifier:8600
      CONSERVATION_C: "2000.0"
      CONSERVATION_ALPHA: "0.1"
    volumes:
      - racks:/data/racks
      - skills:/data/skills

  plato:
    image: openclaw/plato-room:1.0.0
    volumes: [wal:/data/wal]

  hebbian:
    image: openclaw/hebbian:1.0.0

  router:
    image: openclaw/fleet-router:1.0.0

  verifier:
    image: openclaw/content-verifier:1.0.0

  cashew-bridge:
    image: openclaw/cashew-bridge:1.0.0
    profiles: [cashew]
```

### 5.4 Edge Deployment

For latency-critical deployments (sub-50ms tile writes), the Construct supports an edge mode where the shell server, WAL, and GL(9) detector co-locate on edge hardware, with Hebbian service and fleet router as remote services with graceful degradation.

Edge mode relaxes the conservation check to an async background validator when Hebbian service is unreachable, logging provisional violations for reconciliation on reconnect. This is the only context where the conservation law is not enforced synchronously — and only for the H term, not γ or V.

---

## 6. Security

### 6.1 Agent Authentication

Agents authenticate via short-lived signed tokens issued by the fleet router. Tokens carry:
- `agent_id` — stable identifier
- `fleet_domain` — which rack domains the agent may load
- `budget_ceiling` — maximum C constant allowed
- `exp` — expiration (max 24h)

The construct server validates tokens on every write operation, not just at boot. Token refresh is handled by the fleet router's self-healing path; a suspended token triggers shell suspension, not immediate eviction.

### 6.2 Tile Provenance

Every tile in the WAL carries an external verifier signature. The content verifier service maintains a signing key that is independent of both the tile author and the shell server. This enforces the calibration principle: the instrument that wrote the tile cannot be the instrument that attested it.

Tile provenance chain:
```
Author (agent) → Content Verifier (external) → WAL (append-only) → Audit Log
```

The WAL itself is append-only. Once committed, a tile version cannot be modified; only new versions can be appended. Deletion is tombstoning, not erasure — the tombstone is signed by the same external verifier.

### 6.3 Fleet Isolation

Shells are isolated by room_id at the PLATO layer. Cross-shell tile reads require explicit federation tokens. Cross-shell tile writes are not permitted — a tile belongs to exactly one shell for its entire lifecycle.

Rack bundles are shared read-only objects; each shell gets its own tile copies when loading a rack. This ensures that a compromised shell cannot corrupt the rack store used by other shells.

### 6.4 Skill Isolation

Skills run in a restricted execution context with no direct filesystem access and no network access outside the shell's declared endpoint list. Skill invocations are logged to the WAL with full input/output hashes, making skill behavior auditable.

The Hebbian service registration of each skill provides an additional behavioral tripwire: if a skill's Hebbian node begins exhibiting weight patterns inconsistent with its declared behavior, the fleet router receives an anomaly signal and can throttle or quarantine the shell.

### 6.5 Conservation as a Security Invariant

The conservation law γ+H = C − α·ln V is not only a cognitive constraint; it is a security boundary. An attacker attempting to inject a large tile payload (content bomb) will cause V to increase sharply, which reduces the right-hand side budget. The system will begin rejecting further writes before the attacker can exhaust the tile surface. This provides a natural rate-limiting floor against tile flooding attacks without requiring explicit rate limit configuration.

---

## 7. Scalability

### 7.1 Single Agent (ZeroClaw)

One agent, one shell, one room. All services in-process. Target: 50 tile writes/sec, <5ms p99 write latency. Conservation budget: C ≈ 2000 supports ~500 active tiles with typical rack combination.

### 7.2 Small Fleet (2–10 Agents)

Independent shell nodes sharing a Hebbian service and fleet router. Cashew bridge optional. The fleet router's domain-aware routing ensures each agent's tile writes reach the correct shell node without broadcast.

Target: 200 tile writes/sec aggregate, <10ms p99. Hebbian service becomes the bottleneck at this scale; connection pooling required.

### 7.3 Medium Fleet (10–50 Agents)

Horizontal scaling of shell nodes. Hebbian service sharded by shell_id prefix. Content verifier pool with consistent hashing. GL(9) detector is stateless and scales linearly.

The conservation law creates a natural scaling ceiling per shell node: as V approaches the budget, write throughput degrades gracefully rather than failing hard. Operators should monitor `budget_remaining` via the fleet router's health endpoint and add shell nodes proactively.

```
Fleet at 50 agents:
  Shell nodes:      5–10 (5–10 agents per node)
  Hebbian shards:   3
  Verifier pool:    3 (round-robin)
  GL(9) detectors:  2 (active-passive)
  Fleet router:     1 primary + 1 standby
```

### 7.4 Large Fleet (50–100+ Agents)

At this scale, the Cashew bridge becomes the coordination backbone. Shell state is periodically checkpointed to Cashew memory systems, allowing shells to migrate between nodes without losing tile history.

The fleet router's self-healing path handles node failures by replaying the WAL from the last Cashew checkpoint. Recovery time is bounded by WAL replay speed, which is typically under 2 seconds for shells with fewer than 10,000 tile versions.

Target: 2000 tile writes/sec aggregate across 100 agents.

---

## 8. Integration

### 8.1 OpenClaw

OpenClaw agents boot into the Construct via a standard `ShellBootRequest`. The OpenClaw runtime is responsible for providing a valid fleet router token; the Construct does not manage agent lifecycle beyond the shell boundary. OpenClaw agents receive a `ShellHandle` and interact exclusively through the Construct API.

### 8.2 Cashew Memory Systems

The Cashew bridge provides bidirectional docking:
- **Export:** Construct tiles can be pushed to Cashew as memory objects, with tile metadata preserved as Cashew tags.
- **Import:** Cashew memories can be injected as tiles into a shell, with the content verifier acting as the attestation provider (calibration principle: Cashew is external to the Construct).

The bridge exposes `/cashew/push` and `/cashew/pull` endpoints on the Construct, with conflict resolution handled by version vector comparison.

### 8.3 CrewAI

CrewAI agents can be wrapped as Construct-compatible agents by implementing the `AgentDockingProtocol`:

```python
class AgentDockingProtocol:
    async def on_shell_boot(self, shell_handle: ShellHandle) -> None: ...
    async def on_tile_event(self, tile: Tile, event: str) -> None: ...
    async def on_conservation_warning(self, budget_remaining: float) -> None: ...
    async def on_holodeck_swap(self, program: str) -> None: ...
```

CrewAI tasks map to dojo scenarios; CrewAI tools map to injected skills.

### 8.4 MCP (Model Context Protocol)

The Construct exposes an MCP-compatible resource server at `/mcp/resources`. Each active tile is a resource; each bound skill is a tool. MCP clients can read tile content, invoke skills, and subscribe to tile change events via the standard MCP resource subscription mechanism.

The tile surface appears to MCP clients as a flat resource namespace: `construct://{shell_id}/tile/{tile_id}`.

### 8.5 A2A (Agent-to-Agent Protocol)

Agents in separate shells can communicate via the fleet router's A2A relay. Messages are tile writes to a shared relay room; the fleet router mediates access and enforces isolation. A2A messages are subject to the same conservation constraints as regular tile writes — there is no bypass path for inter-agent messages.

---

## 9. Extension Points

### 9.1 Adding a New Rack

A rack is a bundle of tiles with a manifest. To add `fleet-robotics`:

1. Create `/racks/fleet-robotics/manifest.json` with tile definitions, expected V delta, and compatible templates.
2. Submit the bundle to the content verifier for attestation.
3. Register the rack name in the fleet router's domain table.
4. Set `RACK_FLEET_ROBOTICS_URL` in the construct environment.

The rack loader discovers racks by environment variable convention (`RACK_{NAME}_URL`). No code changes to `construct.py` are required.

### 9.2 Adding a New Skill

A skill is a Python callable with a declared interface and an external verifier ID. To add `skill-topology`:

1. Implement the callable conforming to `SkillInterface` (input dict → output dict, no side effects outside tile writes).
2. Register with the Hebbian service to receive a `hebbian_node_id`.
3. Submit for external verification; receive `verifier_signature`.
4. Place the skill module in `/skills/` and set `SKILL_TOPOLOGY_MODULE`.

The skill injector discovers skills by environment variable convention. The calibration principle is enforced at registration: a skill that cannot produce an external verifier ID is rejected.

### 9.3 Adding a Dojo Scenario

A scenario is a Python class conforming to `ScenarioInterface`:

```python
class ScenarioInterface:
    name: str
    def initial_state(self, seed: int, difficulty: int) -> Dict: ...
    def evaluate_action(self, state: Dict, action: Dict) -> Tuple[Dict, float]: ...
    def is_terminal(self, state: Dict) -> bool: ...
    def conservation_impact(self, state: Dict) -> Dict: ...
```

Place the class in `/scenarios/` and register via `SCENARIO_{NAME}_MODULE`. The dojo arena discovers scenarios at startup.

### 9.4 Adding a Holodeck Program

A holodeck program is a rack bundle marked with `holodeck: true` in its manifest. The holodeck controller treats these specially: on `load`, it performs a context swap rather than additive loading. Existing context tiles are evicted (cold) or replaced (hot) based on the `swap_mode` parameter.

To add `program-underwater`: follow the rack bundle process, set `holodeck: true` and `swap_mode_default: hot` in the manifest.

### 9.5 Adding a Shell Template

A template is a YAML configuration file specifying default rack list, default skill list, initial conservation budget, and annealing parameters. Templates live in `/templates/`. The blank template is the identity element — no racks, no skills, C = 1000, alpha = 0.1.

---

## 10. Performance

### 10.1 Latency Budget

| Operation | p50 | p95 | p99 |
|---|---|---|---|
| Shell boot (blank, no racks) | 45ms | 80ms | 120ms |
| Shell boot (3 racks, 2 skills) | 800ms | 1.4s | 2.1s |
| Tile write (active, no fault) | 3ms | 8ms | 15ms |
| Tile write (with GL(9) check) | 6ms | 14ms | 25ms |
| Skill invocation (light) | 4ms | 10ms | 20ms |
| Rack load (fleet-math, ~50 tiles) | 200ms | 400ms | 700ms |
| Holodeck swap (hot) | 80ms | 150ms | 280ms |
| Holodeck swap (cold) | 600ms | 1.1s | 1.8s |
| Dojo step evaluation | 15ms | 30ms | 60ms |
| Conservation check (synchronous) | 2ms | 5ms | 10ms |

The conservation check is the mandatory synchronous gate on every tile write. The Hebbian service query dominates this latency. Operators who require sub-5ms p99 tile writes should deploy the Hebbian service on the same host as the shell node and use Unix domain socket communication.

### 10.2 Throughput

Single shell node (8 vCPU, 16 GB):
- 500 tile writes/sec sustained
- 200 skill invocations/sec sustained
- 50 rack loads/sec (burst, not sustained)
- 20 concurrent shells

Conservation accounting does not add throughput overhead beyond the synchronous check latency. The WAL is the primary throughput ceiling; SQLite WAL mode supports ~2000 writes/sec on NVMe; Postgres WAL mode removes this ceiling.

### 10.3 Memory Profile

| Component | Resident Set |
|---|---|
| construct.py (idle) | 45 MB |
| Per active shell | +8 MB |
| Per loaded rack (average) | +12 MB |
| Per bound skill | +3 MB |
| Tile surface cache (LRU, 1000 tiles) | +60 MB |
| GL(9) fault detector | +20 MB (model weights) |

Fleet deployment target: 2 GB node RAM for 50 concurrent shells with average 2 racks each.

### 10.4 Storage

The WAL is append-only. Storage grows at approximately 2 KB per tile version. A shell with 500 active tiles and typical churn (3 versions per tile per session) consumes ~3 MB per session. With 100 agents running 8-hour sessions, expect ~300 MB WAL growth per day before archival.

The archival process (triggered at shell shutdown) compresses the WAL to ~40% of raw size using zstd. Long-term storage (Cashew) is managed by the Cashew bridge and is outside the Construct's storage budget.

---

## Appendix A: Conservation Law Reference

The deployment form of the conservation law:

```
γ + H = C − α·ln V
```

**Geometric distortion γ** is computed by the PLATO room server as the Frobenius norm of the difference between the current tile layout matrix and the reference (boot-time) layout. High γ indicates the tile surface has deformed significantly from its initial geometry — typically caused by loading racks with conflicting spatial priors.

**Hebbian entropy H** is computed by the Hebbian service as the Shannon entropy of the weight distribution across all active synaptic connections. High H indicates a diffuse, unspecialized connection graph — typical early in a session before skill invocations have reinforced useful connections.

**Conservation constant C** is set at shell boot and never modified. It represents the cognitive budget for the session. Operators choose C based on expected rack combination and session length. C = 1000 is the default; the blank template uses this. Heavy-use shells (all 5 racks + all 5 skills) require C ≥ 2500.

**Annealing coefficient α** controls how quickly the budget shrinks as tile volume grows. Small α (0.05) means the system tolerates large V with minimal budget penalty — appropriate for bulk data loading. Large α (0.5) means the budget shrinks steeply with V — appropriate for sessions where cognitive focus (low V) is critical.

**Tile volume V** is the count of currently active (non-evicted, non-archived) tiles. V is the only term the operator can directly influence during a session by evicting tiles.

---

## Appendix B: Shell Template Reference

| Template | Default Racks | Default Skills | C | α | Description |
|---|---|---|---|---|---|
| blank | none | none | 1000 | 0.1 | Empty shell, no preloads |
| forklift | fleet-math, fleet-translate | eisenstein, translation | 2500 | 0.08 | Heavy data movement |
| sprinter | fleet-reason | hebbian, conservation | 1500 | 0.15 | Fast reasoning, low V |
| service | fleet-health, fleet-comm | fault-detect, hebbian | 2000 | 0.1 | Long-running service agent |

---

## Appendix C: GL(9) Fault Detection Reference

The GL(9) semantic fault detector projects tile semantic vectors onto a 9-dimensional manifold and identifies vectors that fall outside the manifold's valid region (determined during content verifier training). The 9 dimensions correspond to:

1. Semantic coherence (internal consistency of tile content)
2. Contextual alignment (fit with current rack context)
3. Conservation compatibility (whether the tile's geometric weight is consistent with current γ)
4. Temporal consistency (whether the tile's claim is consistent with tile history)
5. Cross-tile entailment (whether the tile contradicts existing tiles)
6. Source diversity (calibration principle: tiles from a single source cluster are flagged)
7. Hebbian alignment (whether the tile would reinforce or contradict current weight structure)
8. Program compatibility (whether the tile fits the active holodeck program context)
9. Fleet consensus (whether peer shells with similar racks have seen this content)

A tile is rejected with `422 SemanticFault` if its projection falls outside the 3σ boundary on any dimension. The fault detector does not explain its rejections in production mode; in debug mode, it returns the dimension index and deviation magnitude.
