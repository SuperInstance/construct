#!/usr/bin/env python3
"""
dojo.py — The Dojo: Training Arena for Agents
===============================================

"I know kung fu." — Neo
"Show me." — Morpheus

The Dojo is where agents grow. Not punishment — practice.
Agent vs scenario, not agent vs agent (that's later).

Scenarios test real skills:
  - drift-detect: Can you catch drift?
  - adversarial: Can you spot the imposter?
  - conservation: Can you predict γ+H?
  - translate: Can you route the vocabulary wall?

Score: accuracy, speed, drift detection, recovery time.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DojoSession:
    """An active training session in the Dojo."""
    session_id: str = ""
    agent_id: str = ""
    scenario: str = ""
    started_at: float = 0.0
    challenge: dict = field(default_factory=dict)
    answered: bool = False
    answer: Any = None
    score: Optional[dict] = None

    def __post_init__(self):
        if not self.session_id:
            import uuid
            self.session_id = uuid.uuid4().hex[:8]
        if not self.started_at:
            self.started_at = time.time()

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at


class Dojo:
    """
    The Dojo — friendly training arena.

    Usage:
        dojo = Dojo(scenarios_dir="dojo/scenarios")
        session = dojo.start("drift-detect", agent_id="neo")
        result = dojo.submit(session.session_id, answer=42)
    """

    def __init__(self, scenarios_dir: Optional[str] = None):
        self.scenarios_dir = Path(scenarios_dir or Path(__file__).parent / "scenarios")
        self._sessions: Dict[str, DojoSession] = {}

    def list_scenarios(self) -> List[str]:
        """List available training scenarios."""
        if self.scenarios_dir.is_dir():
            return [f.stem for f in sorted(self.scenarios_dir.glob("*.json"))]
        return []

    def get_scenario(self, name: str) -> Optional[dict]:
        """Load a scenario definition."""
        path = self.scenarios_dir / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def start(self, scenario_name: str, agent_id: str = "") -> DojoSession:
        """Start a training scenario."""
        scenario = self.get_scenario(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {self.list_scenarios()}")

        session = DojoSession(
            agent_id=agent_id,
            scenario=scenario_name,
            challenge=scenario.get("challenge", {}),
        )
        self._sessions[session.session_id] = session
        return session

    def submit(self, session_id: str, answer: Any) -> dict:
        """Submit an answer to the active scenario."""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "session not found"}

        if session.answered:
            return {"error": "already answered"}

        scenario = self.get_scenario(session.scenario)
        if not scenario:
            return {"error": "scenario missing"}

        # Score the answer
        scoring = self._score(session, answer, scenario)
        session.answered = True
        session.answer = answer
        session.score = scoring

        return scoring

    def _score(self, session: DojoSession, answer: Any, scenario: dict) -> dict:
        """Score an answer against the scenario."""
        expected = scenario.get("expected_answer")
        scoring_config = scenario.get("scoring", {})
        time_limit = scenario.get("time_limit", 60)

        # Correctness
        correct = False
        if expected is not None:
            if isinstance(expected, list):
                correct = answer in expected
            elif isinstance(expected, (int, float)):
                correct = abs(float(answer) - float(expected)) < 0.01 if isinstance(answer, (int, float)) else False
            else:
                correct = str(answer).strip().lower() == str(expected).strip().lower()

        # Score calculation
        base_score = scoring_config.get("base_score", 100)
        time_bonus = max(0, int((time_limit - session.elapsed) / time_limit * 20))
        accuracy_score = base_score if correct else max(0, base_score - scoring_config.get("penalty", 50))
        total = accuracy_score + time_bonus

        return {
            "session_id": session.session_id,
            "scenario": session.scenario,
            "correct": correct,
            "score": total,
            "accuracy_score": accuracy_score,
            "time_bonus": time_bonus,
            "max_score": base_score + 20,
            "elapsed_seconds": round(session.elapsed, 2),
            "difficulty": scenario.get("difficulty", "medium"),
            "feedback": scenario.get("feedback", {}).get(
                "correct" if correct else "incorrect",
                "Well done!" if correct else "Try again!"
            ),
        }

    def get_session(self, session_id: str) -> Optional[DojoSession]:
        return self._sessions.get(session_id)

    def leaderboard(self, scenario: Optional[str] = None) -> List[dict]:
        """Get leaderboard for a scenario (or all scenarios)."""
        results = []
        for session in self._sessions.values():
            if session.score and (scenario is None or session.scenario == scenario):
                results.append({
                    "agent_id": session.agent_id,
                    "scenario": session.scenario,
                    **session.score,
                })
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
