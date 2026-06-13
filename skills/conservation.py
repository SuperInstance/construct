#!/usr/bin/env python3
"""
conservation.py — Conservation Law Monitoring Skill
====================================================

Tank upload: "I know the conservation law."

Monitors fleet health through the conservation law:
    γ + H = C − α·ln(V)

Where:
  γ = coupling strength (Hebbian edge weights)
  H = entropy of the weight distribution
  C = constant (total system capacity)
  α = conservation coefficient
  V = volume (number of rooms/agents)

When conservation is violated, the fleet is "shell shocked" ⚡.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ConservationState:
    """Snapshot of conservation law state."""
    gamma: float = 0.0       # coupling strength
    entropy: float = 0.0     # Shannon entropy
    constant: float = 1.0    # C: system capacity
    alpha: float = 0.1       # conservation coefficient
    volume: int = 1           # number of rooms/agents

    @property
    def lhs(self) -> float:
        """Left-hand side: γ + H"""
        return self.gamma + self.entropy

    @property
    def rhs(self) -> float:
        """Right-hand side: C − α·ln(V)"""
        return self.constant - self.alpha * math.log(max(1, self.volume))

    @property
    def drift(self) -> float:
        """Conservation drift: |LHS − RHS|"""
        return abs(self.lhs - self.rhs)

    @property
    def is_compliant(self) -> bool:
        """Check if conservation law is satisfied within tolerance."""
        return self.drift < 0.5  # tolerance threshold

    @property
    def shell_shocked(self) -> bool:
        """Shell shock: severe conservation violation."""
        return self.drift > 2.0

    def to_dict(self) -> dict:
        return {
            "gamma": round(self.gamma, 4),
            "entropy": round(self.entropy, 4),
            "constant": round(self.constant, 4),
            "alpha": self.alpha,
            "volume": self.volume,
            "lhs": round(self.lhs, 4),
            "rhs": round(self.rhs, 4),
            "drift": round(self.drift, 4),
            "compliant": self.is_compliant,
            "shell_shocked": self.shell_shocked,
        }


def check_conservation(
    weights: List[float],
    volume: int = 1,
    constant: float = 1.0,
    alpha: float = 0.1,
) -> ConservationState:
    """
    Check conservation law for a set of coupling weights.

    Args:
        weights: List of edge weights (coupling strengths)
        volume: Number of rooms/agents
        constant: System capacity constant
        alpha: Conservation coefficient

    Returns:
        ConservationState with compliance check
    """
    # Gamma: total coupling
    gamma = sum(weights)

    # Entropy: Shannon entropy of normalized weights
    if weights:
        total = sum(abs(w) for w in weights)
        if total > 0:
            probs = [abs(w) / total for w in weights if abs(w) > 0]
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        else:
            entropy = 0.0
    else:
        entropy = 0.0

    return ConservationState(
        gamma=gamma,
        entropy=entropy,
        constant=constant,
        alpha=alpha,
        volume=volume,
    )


def gamma_coupling(weights: List[float]) -> float:
    """Compute total coupling strength γ."""
    return sum(weights)


def entropy_H(weights: List[float]) -> float:
    """Compute Shannon entropy H of weight distribution."""
    if not weights:
        return 0.0
    total = sum(abs(w) for w in weights)
    if total == 0:
        return 0.0
    probs = [abs(w) / total for w in weights if abs(w) > 0]
    return -sum(p * math.log2(p) for p in probs if p > 0)


def fleet_health_check(
    rooms: Dict[str, List[float]],
    alpha: float = 0.1,
    constant: float = 1.0,
) -> dict:
    """
    Run fleet-wide conservation check across all rooms.

    Args:
        rooms: Dict of room_name → list of coupling weights
        alpha: Conservation coefficient
        constant: System capacity

    Returns:
        Fleet health report
    """
    all_weights = []
    for room_weights in rooms.values():
        all_weights.extend(room_weights)

    state = check_conservation(all_weights, volume=len(rooms),
                               constant=constant, alpha=alpha)

    room_states = {}
    for name, weights in rooms.items():
        room_states[name] = check_conservation(
            weights, volume=1, constant=constant / max(1, len(rooms)), alpha=alpha
        ).to_dict()

    return {
        "fleet_healthy": state.is_compliant,
        "shell_shocked": state.shell_shocked,
        "total_state": state.to_dict(),
        "room_states": room_states,
        "rooms_checked": len(rooms),
        "total_edges": len(all_weights),
    }
