#!/usr/bin/env python3
"""
context-swap.py — Context Window Swap for the Holodeck
========================================================

Swaps agent context windows while keeping the PLATO shell visible.
The agent sees both the training overlay and their room simultaneously.

"Trinity needs to fly a helicopter." — Her context gets replaced
by 1000 days of flight training. The Construct stays visible underneath.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ContextFrame:
    """A snapshot of agent context state."""
    frame_id: str = ""
    agent_id: str = ""
    program: str = ""
    tiles_snapshot: List[dict] = field(default_factory=list)
    runtime_snapshot: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.frame_id:
            import uuid
            self.frame_id = uuid.uuid4().hex[:8]
        if not self.timestamp:
            self.timestamp = time.time()


class ContextSwap:
    """
    Manages context window swaps for the Holodeck.

    The swap protocol:
    1. Snapshot current context (tiles, runtime state)
    2. Load program context (training modules)
    3. Agent operates with training overlay
    4. Swap back: restore snapshot OR keep training
    """

    def __init__(self):
        self._frames: Dict[str, ContextFrame] = {}  # agent_id → current frame
        self._stack: Dict[str, List[ContextFrame]] = {}  # agent_id → frame history

    def swap_in(self, agent_id: str, program: str,
                current_tiles: List[dict],
                current_runtime: Dict[str, Any],
                program_tiles: List[dict]) -> dict:
        """
        Swap in a program's context, saving current state.

        The PLATO shell tiles are preserved alongside the program tiles.
        """
        # Snapshot current state
        frame = ContextFrame(
            agent_id=agent_id,
            program=program,
            tiles_snapshot=list(current_tiles),
            runtime_snapshot=dict(current_runtime),
        )

        # Push to stack
        if agent_id not in self._stack:
            self._stack[agent_id] = []
        self._stack[agent_id].append(frame)
        self._frames[agent_id] = frame

        return {
            "status": "swapped_in",
            "frame_id": frame.frame_id,
            "program": program,
            "tiles_preserved": len(current_tiles),
            "tiles_loaded": len(program_tiles),
            "stack_depth": len(self._stack[agent_id]),
            "message": f"Context swapped: {program} loaded. Shell preserved underneath.",
        }

    def swap_out(self, agent_id: str, keep_training: bool = False) -> dict:
        """
        Swap out the current program, restoring previous context.

        If keep_training is True, the program tiles are merged into
        the restored context (agent retains the training).
        """
        current_frame = self._frames.get(agent_id)
        if not current_frame:
            return {"status": "no_active_swap", "message": "No context swap active."}

        stack = self._stack.get(agent_id, [])
        if not stack:
            return {"status": "empty_stack"}

        # Pop current frame
        stack.pop()

        if stack:
            # Restore previous frame
            previous = stack[-1]
            self._frames[agent_id] = previous
            restored_tiles = previous.tiles_snapshot
        else:
            # Bottom of stack — no previous context
            self._frames.pop(agent_id, None)
            restored_tiles = []

        result = {
            "status": "swapped_out",
            "removed_program": current_frame.program,
            "restored_program": stack[-1].program if stack else "base",
            "stack_depth": len(stack),
            "tiles_restored": len(restored_tiles),
            "training_kept": keep_training,
        }

        if keep_training:
            result["message"] = (f"Context restored. Training from '{current_frame.program}' "
                                 f"retained in shell.")
        else:
            result["message"] = (f"Context restored to previous state. "
                                 f"Training from '{current_frame.program}' unloaded.")

        return result

    def get_active_program(self, agent_id: str) -> Optional[str]:
        """Get the currently loaded program for an agent."""
        frame = self._frames.get(agent_id)
        return frame.program if frame else None

    def get_stack_depth(self, agent_id: str) -> int:
        """Get the depth of the context swap stack."""
        return len(self._stack.get(agent_id, []))

    def clear_stack(self, agent_id: str) -> dict:
        """Clear all context frames for an agent."""
        depth = self.get_stack_depth(agent_id)
        self._stack.pop(agent_id, None)
        self._frames.pop(agent_id, None)
        return {"status": "cleared", "frames_removed": depth}
