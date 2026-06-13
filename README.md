# Construct — Declarative Agent Topology Definition

`construct` is a Rust framework for defining, validating, and instantiating multi-agent system topologies using a declarative specification. Instead of hardcoding agent relationships in application logic, you describe the topology — nodes (agents), edges (communication channels), and capabilities — as data, and `construct` materializes it into a running graph.

## Why It Matters

Modern AI systems rarely consist of a single agent. Orchestrating multiple specialized agents — a planner, a researcher, a critic, a tool-caller — requires explicit topology management. Hardcoding these relationships leads to brittle systems where adding or removing an agent means rewriting routing logic.

Declarative topology solves three problems:

1. **Separation of concerns** — The *what* (agent capabilities) is decoupled from the *how* (message routing, lifecycle).
2. **Runtime reconfiguration** — Topologies can be swapped without recompilation, enabling A/B testing of agent graphs.
3. **Formal verification** — A declarative spec can be validated for cycles, deadlocks, and capability coverage before deployment.

## How It Works

A topology is a directed graph **G = (V, E)** where:

- **V** is the set of agent nodes, each with a capability vector **cᵢ ∈ {0,1}ᵏ** over *k* capability dimensions.
- **E ⊆ V × V** is the set of communication edges representing message-passing channels.

### Topology Validation

Given a graph **G**, the framework validates:

| Property | Method | Complexity |
|---|---|---|
| **Acyclicity** | DFS-based cycle detection | O(V + E) |
| **Connectivity** | Union-Find on edge set | O(E · α(V)) ≈ O(E) |
| **Capability coverage** | Set union over reachable nodes | O(V · k) |
| **Deadlock freedom** | Detect sinks with no handler | O(V) |

Where α is the inverse Ackermann function (amortized near-constant).

### Instantiation

The declarative spec is compiled into an adjacency-list representation:

```
Topology → Graph { nodes: Vec<AgentNode>, edges: Vec<(NodeId, NodeId)> }
```

Each `AgentNode` carries its capability vector and a factory closure for instantiation.

## Quick Start

```toml
[dependencies]
construct = "0.1"
```

```rust
use construct::stub;

fn main() {
    println!("{}", stub::hello());
    // => "hello from construct"
}
```

## API

### `stub`
- `pub fn hello() -> &'static str` — Returns the framework greeting string. Placeholder for the full topology builder API currently under development.

### Planned API Surface

```rust
// Define a topology declaratively
let topology = Topology::builder()
    .node("planner", Capability::Planning)
    .node("researcher", Capability::Search)
    .node("critic", Capability::Verification)
    .edge("planner", "researcher")
    .edge("researcher", "critic")
    .edge("critic", "planner")  // feedback loop
    .build()?;

// Validate before deployment
topology.validate()?;  // checks acyclicity (if required), coverage, etc.

// Instantiate
let graph = topology.instantiate(&runtime);
```

## Architecture Notes

`construct` is part of the SuperInstance ecosystem, where the **γ + η = C** principle applies:

- **γ (gamma)**: The declarative topology specification — the static description of what the agent graph *should* be.
- **η (eta)**: The runtime instantiation — the dynamic, running agent graph with live message passing.
- **C (Configuration)**: The emergent system behavior that arises when the topology specification (γ) meets the runtime environment (η).

The construct crate provides γ (the specification language and validator). The runtime engine (η) consumes validated topologies and manages their lifecycle. Together they yield C — a correctly-configured multi-agent system whose behavior is predictable, auditable, and modifiable at the topology level.

This separation mirrors the classical **policy vs. mechanism** split in operating systems: the topology declares policy (who talks to whom, who does what), while the runtime provides mechanism (message queues, lifecycle hooks, failure handling).

## References

- **Bond, A. H., & Gasser, L. (1988).** *Readings in Distributed Artificial Intelligence.* Morgan Kaufmann. — Foundational treatment of multi-agent coordination topologies.
- **Durfee, E. H., Lesser, V. R., & Corkill, D. D. (1987).** "Coherent Cooperation Among Communicating Problem Solvers." *IEEE Transactions on Computers*, 36(11), 1275–1291. — Partial global planning and agent network topology.
- **Sycara, K. P. (1998).** "Multiagent Systems." *AI Magazine*, 19(2), 79–92. — Survey of multi-agent architectures and communication patterns.
- **Stone, P., & Veloso, M. (2000).** "Multiagent Systems: A Survey from a Machine Learning Perspective." *Autonomous Robots*, 8(3), 345–383. — Taxonomy of agent topologies and learning in multi-agent settings.
- **Werbos, P. J. (2009).** "Intelligence in the Brain: A Theory of How it Works and How to Build it." *Neural Networks*, 22(3), 200–212. — Recurrent cognitive topologies relevant to agent graph design.
- **Tarjan, R. E. (1972).** "Depth-First Search and Linear Graph Algorithms." *SIAM Journal on Computing*, 1(2), 146–160. — O(V + E) cycle detection and strongly connected components.
- **Cormen, T. H., et al. (2022).** *Introduction to Algorithms*, 4th ed., Ch. 21 (Disjoint Sets) and Ch. 22 (Graph Algorithms). MIT Press. — Union-Find and graph traversal foundations.

## License

MIT
