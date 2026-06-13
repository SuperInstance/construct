#!/usr/bin/env python3
"""
dojo-scoring.py — Dojo Scoring Engine
======================================

Scores agent performance across training scenarios.
Tracks accuracy, speed, drift detection, and recovery metrics.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentScore:
    """Cumulative score for an agent across scenarios."""
    agent_id: str = ""
    scenarios_completed: int = 0
    total_score: int = 0
    max_possible: int = 0
    correct_count: int = 0
    total_time: float = 0.0
    scenario_breakdown: Dict[str, dict] = field(default_factory=dict)
    badges: List[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if self.scenarios_completed == 0:
            return 0.0
        return self.correct_count / self.scenarios_completed

    @property
    def avg_score(self) -> float:
        if self.scenarios_completed == 0:
            return 0.0
        return self.total_score / self.scenarios_completed

    @property
    def avg_time(self) -> float:
        if self.scenarios_completed == 0:
            return 0.0
        return self.total_time / self.scenarios_completed

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "scenarios_completed": self.scenarios_completed,
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "accuracy": round(self.accuracy, 4),
            "avg_score": round(self.avg_score, 2),
            "avg_time": round(self.avg_time, 2),
            "badges": self.badges,
            "scenario_breakdown": self.scenario_breakdown,
        }


class DojoScoring:
    """Score tracking and badge awarding for the Dojo."""

    def __init__(self):
        self._scores: Dict[str, AgentScore] = {}

    def get_score(self, agent_id: str) -> AgentScore:
        if agent_id not in self._scores:
            self._scores[agent_id] = AgentScore(agent_id=agent_id)
        return self._scores[agent_id]

    def record_result(self, agent_id: str, scenario: str,
                      correct: bool, score: int, max_score: int,
                      elapsed: float, difficulty: str = "medium") -> AgentScore:
        """Record a training result and award badges."""
        agent = self.get_score(agent_id)

        agent.scenarios_completed += 1
        agent.total_score += score
        agent.max_possible += max_score
        agent.total_time += elapsed
        if correct:
            agent.correct_count += 1

        agent.scenario_breakdown[scenario] = {
            "correct": correct,
            "score": score,
            "max_score": max_score,
            "elapsed": round(elapsed, 2),
            "difficulty": difficulty,
        }

        # Award badges
        self._check_badges(agent, scenario, correct, score, elapsed, difficulty)

        return agent

    def _check_badges(self, agent: AgentScore, scenario: str,
                      correct: bool, score: int, elapsed: float,
                      difficulty: str) -> None:
        """Check and award badges based on performance."""
        # First completion
        if agent.scenarios_completed == 1:
            agent.badges.append("🥋 First Steps")

        # Perfect score
        if correct and score >= 100:
            agent.badges.append(f"🎯 Sharpshooter: {scenario}")

        # Speed demon
        if correct and elapsed < 5.0:
            agent.badges.append("⚡ Speed Demon")

        # All correct
        if agent.accuracy == 1.0 and agent.scenarios_completed >= 4:
            agent.badges.append("🏆 Flawless")

        # Hard scenario cleared
        if correct and difficulty == "hard":
            agent.badges.append(f"💀 Hard Mode: {scenario}")

        # Deduplicate badges
        seen = set()
        unique = []
        for b in agent.badges:
            if b not in seen:
                seen.add(b)
                unique.append(b)
        agent.badges = unique

    def leaderboard(self) -> List[dict]:
        """Get sorted leaderboard."""
        results = [s.to_dict() for s in self._scores.values()]
        return sorted(results, key=lambda x: x["total_score"], reverse=True)
