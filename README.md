# construct — Declarative Agent Topology Definition

**construct** is a Rust library for defining agent network topologies declaratively — specifying how agents are connected, what communication layers they participate in, and how coordination messages flow between them. It provides the `CoordNode` and `CoordMessage` primitives that higher-level fleet components (like `fleet-conductor` and `construct-coordination`) build upon to implement actual coordination protocols.

## Why It Matters

In distributed agent systems, topology is destiny. The connection pattern between agents determines which information reaches whom, how fast consensus forms, and whether the system can survive node failures. Hardcoding topology in application logic makes reconfiguration painful and testing impossible. By making topology a **declarative first-class concept**, construct enables fleet operators to rewire agent networks without touching agent code, swap topologies for different deployment scenarios (star for centralized, mesh for resilient, hierarchical for scaled), and simulate topology changes before applying them to production. The library's layer-based addressing mirrors the OSI model — agents operate at specific layers and only see peers in their layer.

## How It Works

### Coordination Nodes

A `CoordNode` represents an agent in the coordination network. Each node has:
- **`id`**: Unique identifier (String)
- **`layer`**: Network layer (0–255), analogous to OSI layers. Layer 0 = physical/transport agents, Layer 1 = service agents, Layer 2 = orchestration agents.
- **`peers`**: List of connected node IDs.

Nodes are constructed with `CoordNode::new(id, layer)` and peers are added incrementally. This mirrors how real network topologies are built — first nodes exist, then connections form.

### Coordination Messages

Messages carry a sequence number for ordering, a payload (raw bytes for protocol flexibility), and source/destination addresses:

```rust
CoordMessage {
    from: "agent-1".into(),
    to: "agent-2".into(),
    payload: vec![...],  // serialized protocol data
    seq: 42,             // monotonic sequence number
}
```

The sequence number enables **causal ordering** — receivers can detect gaps (missing messages) and reorder out-of-order deliveries. This is essential in distributed systems where network jitter can reorder messages (the same problem addressed by TCP sequence numbers).

### Topology Patterns

The layer abstraction naturally supports common topology patterns:

| Topology | Layer Assignment | Connection Pattern |
|----------|-----------------|-------------------|
| **Star** | Hub at layer 2, spokes at layer 0 | Each spoke peers with hub only |
| **Mesh** | All nodes at layer 1 | Every node peers with every other |
| **Hierarchical** | Layers 0, 1, 2, ... | Each node peers with parent and children |
| **Ring** | All at layer 0 | Node $i$ peers with $i-1$ and $i+1$ |

### Complexity

| Operation | Cost |
|-----------|------|
| Node creation | $O(1)$ |
| Peer addition | $O(1)$ amortized (Vec push) |
| Message routing (direct) | $O(1)$ lookup by ID |
| Full topology serialization | $O(V + E)$ where $V$ = nodes, $E$ = edges |
| Broadcast (layer-scoped) | $O(k)$ where $k$ = nodes in layer |

## Quick Start

```rust
use construct::stub;

fn main() {
    println!("{}", stub::hello());
    // "hello from construct"
}

// Define a topology
use construct_coordination::types::{CoordNode, CoordMessage};

fn build_star_topology() {
    let mut hub = CoordNode::new("hub", 2);
    let mut spoke1 = CoordNode::new("spoke-1", 0);
    let mut spoke2 = CoordNode::new("spoke-2", 0);

    hub.peers.push("spoke-1".into());
    hub.peers.push("spoke-2".into());
    spoke1.peers.push("hub".into());
    spoke2.peers.push("hub".into());

    // Send a coordination message
    let msg = CoordMessage {
        from: "hub".into(),
        to: "spoke-1".into(),
        payload: b"INITIALIZE".to_vec(),
        seq: 1,
    };
}
```

```bash
# Build
git clone https://github.com/SuperInstance/construct.git
cd construct
cargo build --release

# Test
cargo test
```

## API

```rust
// src/lib.rs

/// Coordination node in the Construct network.
pub struct CoordNode {
    pub id: String,
    pub layer: u8,
    pub peers: Vec<String>,
}

impl CoordNode {
    pub fn new(id: impl Into<String>, layer: u8) -> Self;
}

/// Coordination message between nodes.
pub struct CoordMessage {
    pub from: String,
    pub to: String,
    pub payload: Vec<u8>,
    pub seq: u64,
}
```

## Architecture Notes

construct is the **topology specification layer** in the SuperInstance fleet stack. It sits below `fleet-conductor` (which orchestrates runtime behavior) and `construct-coordination` (which runs experiments). In the γ + η = C framework, topology determines the propagation dynamics of ternary actions: a star topology concentrates γ at the hub (centralized decision-making), while a mesh topology distributes γ across all nodes (emergent decision-making). The layer abstraction maps to η — more layers means more diverse communication patterns, increasing the system's entropy budget.

See: [SuperInstance Architecture](https://github.com/SuperInstance/SuperInstance/blob/main/ARCHITECTURE.md)

## References

1. Lamport, L. (1978). "Time, Clocks, and the Ordering of Events in a Distributed System." *CACM* 21(7) — The sequence-number ordering scheme used in CoordMessage.
2. De Wolf, T. & Holvoet, T. (2005). "Emergence Versus Self-Organisation: Different Concepts but Promising When Combined." *Engineering Self-Organising Systems* — How topology influences emergent behavior in multi-agent systems.

## License

MIT
