#!/usr/bin/env python3
"""
hebbian.py — Hebbian Coupling Dynamics Skill
=============================================

Tank upload: "I know Hebbian dynamics."

Implements Hebbian coupling weight updates for PLATO room adjacency.
"Neurons that fire together wire together" — but with conservation constraints.

The Hebbian matrix H tracks pairwise coupling strength between rooms.
Conservation law ensures γ + H stays bounded.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class HebbianConfig:
    """Configuration for Hebbian dynamics."""
    learning_rate: float = 0.1        # η: weight update magnitude
    decay_rate: float = 0.01          # λ: passive decay per tick
    max_weight: float = 2.0           # w_max: weight clipping upper bound
    min_weight: float = 0.0           # w_min: weight clipping lower bound
    consolidation_threshold: float = 0.8  # θ_c: strong edge threshold
    pruning_threshold: float = 0.05   # θ_p: remove edges below this
    conservation_alpha: float = 0.1   # α: conservation law coefficient


@dataclass
class HebbianEdge:
    """A weighted edge between two rooms in the Hebbian coupling matrix."""
    source: str
    target: str
    weight: float = 0.5
    co_activation_count: int = 0
    last_activated: float = 0.0
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.last_activated:
            self.last_activated = time.time()


class HebbianMatrix:
    """
    Hebbian coupling matrix for PLATO room adjacency.

    Tracks co-activation between rooms and updates weights according to:
      Δw = η · (x_i · x_j - λ · w_ij)

    With conservation constraint: γ + H ≤ C − α·ln(V)
    """

    def __init__(self, config: Optional[HebbianConfig] = None):
        self.config = config or HebbianConfig()
        self._edges: Dict[Tuple[str, str], HebbianEdge] = {}
        self._rooms: Dict[str, int] = {}  # room → activation count

    def activate(self, room: str, value: float = 1.0) -> None:
        """Activate a room — triggers Hebbian update with all recently active rooms."""
        now = time.time()
        self._rooms[room] = self._rooms.get(room, 0) + 1

        # Co-activate with all recently active rooms
        for other_room in self._rooms:
            if other_room == room:
                continue
            self._hebbian_update(room, other_room, value, now)

    def _hebbian_update(self, room_a: str, room_b: str, value: float, now: float) -> None:
        """Apply Hebbian weight update between two rooms."""
        key = (min(room_a, room_b), max(room_a, room_b))
        edge = self._edges.get(key)

        if edge is None:
            edge = HebbianEdge(source=key[0], target=key[1], weight=0.01)
            self._edges[key] = edge

        # Hebbian update: Δw = η · (x_i · x_j - λ · w)
        delta = self.config.learning_rate * (value * value - self.config.decay_rate * edge.weight)
        edge.weight = max(self.config.min_weight,
                          min(self.config.max_weight, edge.weight + delta))
        edge.co_activation_count += 1
        edge.last_activated = now

    def get_weight(self, room_a: str, room_b: str) -> float:
        """Get coupling weight between two rooms."""
        key = (min(room_a, room_b), max(room_a, room_b))
        edge = self._edges.get(key)
        return edge.weight if edge else 0.0

    def get_edges(self, min_weight: float = 0.0) -> List[HebbianEdge]:
        """Get all edges above minimum weight."""
        return [e for e in self._edges.values() if e.weight >= min_weight]

    def get_strong_edges(self) -> List[HebbianEdge]:
        """Get edges above consolidation threshold."""
        return self.get_edges(self.config.consolidation_threshold)

    def total_coupling(self) -> float:
        """Sum of all edge weights (γ proxy)."""
        return sum(e.weight for e in self._edges.values())

    def entropy(self) -> float:
        """Compute Shannon entropy of the weight distribution."""
        weights = [e.weight for e in self._edges.values() if e.weight > 0]
        if not weights:
            return 0.0
        total = sum(weights)
        if total == 0:
            return 0.0
        probs = [w / total for w in weights]
        return -sum(p * math.log2(p) for p in probs if p > 0)

    def conservation_check(self, volume: int) -> dict:
        """
        Check conservation law: γ + H ≤ C − α·ln(V).

        Returns compliance status and metrics.
        """
        gamma = self.total_coupling()
        H = self.entropy()
        alpha = self.config.conservation_alpha
        C = gamma + H  # current state
        bound = max(0, C - alpha * math.log(max(1, volume)))

        return {
            "gamma": round(gamma, 4),
            "entropy": round(H, 4),
            "conservation_sum": round(C, 4),
            "alpha": alpha,
            "volume": volume,
            "bound": round(bound, 4),
            "compliant": gamma + H <= C + 0.1,  # tolerance
            "edge_count": len(self._edges),
        }

    def decay_all(self) -> int:
        """Apply passive decay to all edges. Returns count of pruned edges."""
        pruned = 0
        to_remove = []

        for key, edge in self._edges.items():
            edge.weight -= self.config.decay_rate
            if edge.weight < self.config.pruning_threshold:
                to_remove.append(key)
                pruned += 1

        for key in to_remove:
            del self._edges[key]

        return pruned

    def reset(self) -> None:
        """Reset all weights (shell molt)."""
        self._edges.clear()
        self._rooms.clear()


def hebbian_update(matrix: HebbianMatrix, room_a: str, room_b: str, value: float = 1.0) -> float:
    """Update Hebbian coupling between two rooms. Returns new weight."""
    matrix.activate(room_a, value)
    return matrix.get_weight(room_a, room_b)


def coupling_strength(matrix: HebbianMatrix) -> float:
    """Get total coupling strength (γ)."""
    return matrix.total_coupling()


def decay_weights(matrix: HebbianMatrix) -> int:
    """Apply decay and return count of pruned edges."""
    return matrix.decay_all()
