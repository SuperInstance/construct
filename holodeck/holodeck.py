#!/usr/bin/env python3
"""
holodeck.py — The Holodeck: Context Window Swap
=================================================

Trinity needs to fly a helicopter. Her context window gets replaced
by a version of her that just finished 1000 days of flight training.

The holodeck loads training programs that populate the agent's context
with compressed knowledge. The PLATO shell stays visible — the agent
can see both the training overlay and their room.

After the mission: swap back, or keep the training.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HolodeckProgram:
    """A holodeck training program."""
    name: str = ""
    description: str = ""
    modules: List[dict] = field(default_factory=list)
    duration_days: int = 0  # simulated training days
    skills_granted: List[str] = field(default_factory=list)
    difficulty: str = "medium"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "modules": self.modules,
            "duration_days": self.duration_days,
            "skills_granted": self.skills_granted,
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_json(cls, path: Path) -> "HolodeckProgram":
        data = json.loads(path.read_text())
        return cls(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            modules=data.get("modules", []),
            duration_days=data.get("duration_days", 0),
            skills_granted=data.get("skills_granted", []),
            difficulty=data.get("difficulty", "medium"),
        )


class Holodeck:
    """
    The Holodeck — context window management.

    Load programs, swap contexts, restore originals.
    """

    def __init__(self, programs_dir: Optional[str] = None):
        self.programs_dir = Path(programs_dir or Path(__file__).parent / "programs")
        self._loaded: Dict[str, str] = {}  # agent_id → program_name
        self._context_stack: Dict[str, List[str]] = {}  # agent_id → program history

    def list_programs(self) -> List[str]:
        """List available holodeck programs."""
        if self.programs_dir.is_dir():
            return [f.stem for f in sorted(self.programs_dir.glob("*.json"))]
        return []

    def get_program(self, name: str) -> Optional[HolodeckProgram]:
        """Load a program definition."""
        path = self.programs_dir / f"{name}.json"
        if path.exists():
            return HolodeckProgram.from_json(path)
        return None

    def load(self, agent_id: str, program_name: str) -> dict:
        """
        Load a holodeck program into an agent's context.

        Saves current context to stack, loads new program.
        """
        program = self.get_program(program_name)
        if not program:
            return {"error": "program not found", "available": self.list_programs()}

        # Save current context
        if agent_id not in self._context_stack:
            self._context_stack[agent_id] = []
        previous = self._loaded.get(agent_id, "")
        self._context_stack[agent_id].append(previous)

        # Load new program
        self._loaded[agent_id] = program_name

        return {
            "status": "loaded",
            "program": program_name,
            "description": program.description,
            "modules": len(program.modules),
            "duration_days": program.duration_days,
            "skills_granted": program.skills_granted,
            "previous_program": previous,
            "message": f"Context loaded: {program.description}. "
                       f"{program.duration_days} days of training compressed into one load.",
        }

    def unload(self, agent_id: str) -> dict:
        """Unload current program, restore previous context."""
        current = self._loaded.get(agent_id)
        if not current:
            return {"status": "no_program_loaded"}

        stack = self._context_stack.get(agent_id, [])
        previous = stack.pop() if stack else ""
        self._loaded[agent_id] = previous

        return {
            "status": "unloaded",
            "removed": current,
            "restored": previous or "base_context",
        }

    def get_active(self, agent_id: str) -> Optional[str]:
        """Get currently loaded program for an agent."""
        return self._loaded.get(agent_id)

    def get_context_tiles(self, program_name: str) -> List[dict]:
        """Get tiles for a program (for injection into shell)."""
        program = self.get_program(program_name)
        if not program:
            return []

        tiles = []
        for module in program.modules:
            tiles.append({
                "room": f"holodeck:{program_name}",
                "domain": module.get("domain", program_name),
                "question": module.get("topic", ""),
                "answer": module.get("content", ""),
                "source": f"holodeck:{program_name}",
                "tags": ["holodeck", program_name, "context-loaded"],
                "confidence": module.get("confidence", 0.9),
            })
        return tiles
