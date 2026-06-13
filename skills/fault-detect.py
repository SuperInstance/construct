#!/usr/bin/env python3
"""
fault-detect.py — Triple Fault Detection Skill
================================================

Tank upload: "I know fault detection."

Implements triple fault detection for fleet agents:
1. GL(9) holonomy consensus — are agents agreeing?
2. Hebbian coupling deviation — is the coupling matrix drifting?
3. Conservation violation — has γ+H escaped bounds?

If all three detect a fault → quarantine the agent.
If two agree → flag for review.
If one detects → monitor closely.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class FaultLevel(Enum):
    """Fault severity level."""
    NONE = 0       # No fault detected
    MONITOR = 1    # One detector flagged — monitor closely
    REVIEW = 2     # Two detectors agree — flag for review
    QUARANTINE = 3 # All three agree — quarantine immediately


@dataclass
class FaultReport:
    """Result of a triple fault detection check."""
    agent_id: str
    level: FaultLevel = FaultLevel.NONE
    gl9_fault: bool = False
    hebbian_fault: bool = False
    conservation_fault: bool = False
    gl9_detail: dict = field(default_factory=dict)
    hebbian_detail: dict = field(default_factory=dict)
    conservation_detail: dict = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    @property
    def fault_count(self) -> int:
        return sum([self.gl9_fault, self.hebbian_fault, self.conservation_fault])

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "level": self.level.name,
            "fault_count": self.fault_count,
            "gl9_fault": self.gl9_fault,
            "hebbian_fault": self.hebbian_fault,
            "conservation_fault": self.conservation_fault,
            "gl9_detail": self.gl9_detail,
            "hebbian_detail": self.hebbian_detail,
            "conservation_detail": self.conservation_detail,
            "timestamp": self.timestamp,
        }


def detect_faults(
    agent_id: str,
    agent_outputs: List[dict],
    coupling_weights: List[float],
    volume: int = 1,
    consensus_threshold: float = 0.7,
    coupling_drift_threshold: float = 0.5,
    conservation_tolerance: float = 0.5,
) -> FaultReport:
    """
    Run triple fault detection on an agent.

    Args:
        agent_id: Agent identifier
        agent_outputs: List of agent output dicts (for GL(9) consensus)
        coupling_weights: Edge weights (for Hebbian + conservation)
        volume: Number of rooms (for conservation)
        consensus_threshold: Minimum pairwise agreement
        coupling_drift_threshold: Maximum acceptable weight variance
        conservation_tolerance: Maximum conservation drift

    Returns:
        FaultReport with severity level
    """
    report = FaultReport(agent_id=agent_id)

    # Check 1: GL(9) consensus — are outputs internally consistent?
    gl9_result = _check_gl9_consensus(agent_outputs, consensus_threshold)
    report.gl9_fault = not gl9_result["consistent"]
    report.gl9_detail = gl9_result

    # Check 2: Hebbian coupling — is weight distribution healthy?
    hebbian_result = _check_hebbian_health(coupling_weights, coupling_drift_threshold)
    report.hebbian_fault = not hebbian_result["healthy"]
    report.hebbian_detail = hebbian_result

    # Check 3: Conservation law — is γ+H within bounds?
    conservation_result = _check_conservation(coupling_weights, volume, conservation_tolerance)
    report.conservation_fault = not conservation_result["compliant"]
    report.conservation_detail = conservation_result

    # Determine severity from fault count
    if report.fault_count >= 3:
        report.level = FaultLevel.QUARANTINE
    elif report.fault_count >= 2:
        report.level = FaultLevel.REVIEW
    elif report.fault_count >= 1:
        report.level = FaultLevel.MONITOR
    else:
        report.level = FaultLevel.NONE

    return report


def triple_check(
    agent_id: str,
    outputs: List[dict],
    weights: List[float],
    volume: int = 1,
) -> FaultReport:
    """Convenience function: run all three checks."""
    return detect_faults(agent_id, outputs, weights, volume)


def quarantine(report: FaultReport) -> dict:
    """
    Quarantine an agent based on fault report.

    Returns quarantine action details.
    """
    if report.level != FaultLevel.QUARANTINE:
        return {"action": "none", "reason": f"fault level is {report.level.name}"}

    return {
        "action": "quarantine",
        "agent_id": report.agent_id,
        "reason": f"Triple fault detected: GL(9)={report.gl9_fault}, "
                  f"Hebbian={report.hebbian_fault}, Conservation={report.conservation_fault}",
        "fault_count": report.fault_count,
        "timestamp": time.time(),
        "recovery_protocol": "Isolate agent, drain pending work, restart with fresh shell.",
    }


# -- Internal checkers --------------------------------------------------

def _check_gl9_consensus(outputs: List[dict], threshold: float) -> dict:
    """Check if agent outputs are internally consistent (GL(9) proxy)."""
    if len(outputs) < 2:
        return {"consistent": True, "reason": "insufficient_data", "pairwise_agreement": 1.0}

    # Compute pairwise confidence similarity
    confidences = [o.get("confidence", 0.5) for o in outputs]
    if not confidences:
        return {"consistent": True, "pairwise_agreement": 1.0}

    # Variance-based check: high variance = inconsistent
    mean_conf = sum(confidences) / len(confidences)
    variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
    agreement = 1.0 - min(1.0, variance * 4)  # scale variance to [0,1]

    return {
        "consistent": agreement >= threshold,
        "pairwise_agreement": round(agreement, 4),
        "mean_confidence": round(mean_conf, 4),
        "variance": round(variance, 4),
    }


def _check_hebbian_health(weights: List[float], drift_threshold: float) -> dict:
    """Check if Hebbian coupling distribution is healthy."""
    if not weights:
        return {"healthy": True, "reason": "no_weights"}

    mean_w = sum(weights) / len(weights)
    variance = sum((w - mean_w) ** 2 for w in weights) / len(weights)
    std_dev = math.sqrt(variance)

    # Health: standard deviation within bounds
    healthy = std_dev <= drift_threshold

    return {
        "healthy": healthy,
        "mean_weight": round(mean_w, 4),
        "std_dev": round(std_dev, 4),
        "drift_threshold": drift_threshold,
        "weight_count": len(weights),
    }


def _check_conservation(weights: List[float], volume: int, tolerance: float) -> dict:
    """Check conservation law compliance."""
    if not weights:
        return {"compliant": True, "reason": "no_weights"}

    gamma = sum(weights)

    # Entropy
    total = sum(abs(w) for w in weights)
    if total > 0:
        probs = [abs(w) / total for w in weights if abs(w) > 0]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    else:
        entropy = 0.0

    # Simple check: gamma + entropy should be bounded
    conservation_value = gamma + entropy
    bound = max(1.0, 10.0 * math.log(max(1, volume)))

    return {
        "compliant": conservation_value <= bound + tolerance,
        "gamma": round(gamma, 4),
        "entropy": round(entropy, 4),
        "conservation_value": round(conservation_value, 4),
        "bound": round(bound, 4),
        "tolerance": tolerance,
    }
