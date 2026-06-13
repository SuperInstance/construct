#!/usr/bin/env python3
"""
tests/test_construct.py — Test Suite for The Construct
======================================================

20+ tests covering: server boot, shell creation, rack loading,
skill injection, dojo training, holodeck programs, context swap,
tile management, cleanup, and edge cases.
"""

import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from construct import (
    Tile, Shell, ConstructState, ConstructHandler, load_config,
    BASE_DIR, DEFAULT_CONFIG,
)
# Import dojo/holodeck/skills by path since they're not packages
import importlib.util

def _import_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

dojo_mod = _import_from_path("dojo", BASE_DIR / "dojo" / "dojo.py")
dojo_scoring_mod = _import_from_path("dojo_scoring", BASE_DIR / "dojo" / "dojo-scoring.py")
holodeck_mod = _import_from_path("holodeck", BASE_DIR / "holodeck" / "holodeck.py")
context_swap_mod = _import_from_path("context_swap", BASE_DIR / "holodeck" / "context-swap.py")

Dojo = dojo_mod.Dojo
DojoScoring = dojo_scoring_mod.DojoScoring
AgentScore = dojo_scoring_mod.AgentScore
Holodeck = holodeck_mod.Holodeck
ContextSwap = context_swap_mod.ContextSwap


class TestTile(unittest.TestCase):
    """Test MythosTile-compatible tile protocol."""

    def test_tile_creation_defaults(self):
        tile = Tile(room="test", question="Hello?")
        self.assertTrue(tile.tile_id)
        self.assertTrue(tile.timestamp > 0)
        self.assertTrue(tile.tile_hash)
        self.assertEqual(tile.lifecycle, "active")
        self.assertEqual(tile.tags, [])
        self.assertEqual(tile.confidence, 1.0)

    def test_tile_roundtrip(self):
        tile = Tile(
            room="forge", domain="math", question="Compute norm",
            answer="7", source="test", tags=["math"],
            confidence=0.95, agent_id="forgemaster",
        )
        d = tile.to_dict()
        tile2 = Tile.from_dict(d)
        self.assertEqual(tile.tile_id, tile2.tile_id)
        self.assertEqual(tile.room, tile2.room)
        self.assertEqual(tile.question, tile2.question)
        self.assertEqual(tile.answer, tile2.answer)
        self.assertEqual(tile.confidence, tile2.confidence)

    def test_tile_custom_id(self):
        tile = Tile(tile_id="my-custom-id", room="test")
        self.assertEqual(tile.tile_id, "my-custom-id")

    def test_tile_hash_deterministic(self):
        t1 = Tile(room="x", question="y", answer="z", source="s", tile_id="id1")
        t2 = Tile(room="x", question="y", answer="z", source="s", tile_id="id2")
        # Same content → same hash (tile_id differs but hash is content-based)
        self.assertEqual(t1.tile_hash, t2.tile_hash)


class TestShell(unittest.TestCase):
    """Test shell lifecycle."""

    def test_shell_creation(self):
        shell = Shell(agent_id="agent-1", agent_name="Test")
        self.assertTrue(shell.session_id)
        self.assertTrue(shell.room.startswith("construct-"))
        self.assertEqual(shell.loaded_racks, [])
        self.assertEqual(shell.loaded_skills, [])

    def test_shell_touch(self):
        shell = Shell(agent_id="agent-1")
        old = shell.last_active
        time.sleep(0.01)
        shell.touch()
        self.assertGreater(shell.last_active, old)

    def test_shell_to_dict(self):
        shell = Shell(agent_id="agent-1", agent_name="Test", shell_type="forklift")
        d = shell.to_dict()
        self.assertEqual(d["agent_id"], "agent-1")
        self.assertEqual(d["shell_type"], "forklift")
        self.assertIn("tile_count", d)
        self.assertIn("loaded_racks", d)


class TestConstructState(unittest.TestCase):
    """Test the core server state management."""

    def setUp(self):
        self.config = load_config(str(BASE_DIR / "construct.json"))
        self.state = ConstructState(self.config)

    def test_create_shell(self):
        shell = self.state.create_shell("agent-1", "TestAgent")
        self.assertEqual(shell.agent_id, "agent-1")
        self.assertEqual(shell.agent_name, "TestAgent")
        self.assertIn(shell.session_id, self.state.shells)

    def test_create_shell_dedup(self):
        s1 = self.state.create_shell("agent-1", "Test")
        s2 = self.state.create_shell("agent-1", "Test")
        self.assertEqual(s1.session_id, s2.session_id)

    def test_get_shell_by_agent(self):
        shell = self.state.create_shell("agent-1", "Test")
        found = self.state.get_shell_by_agent("agent-1")
        self.assertEqual(found.session_id, shell.session_id)

    def test_remove_shell(self):
        shell = self.state.create_shell("agent-1", "Test")
        removed = self.state.remove_shell(shell.session_id)
        self.assertEqual(removed.session_id, shell.session_id)
        self.assertIsNone(self.state.get_shell(shell.session_id))
        self.assertIsNone(self.state.get_shell_by_agent("agent-1"))

    def test_load_rack(self):
        shell = self.state.create_shell("agent-1", "Test")
        result = self.state.load_rack(shell.session_id, "fleet-math")
        self.assertEqual(result["status"], "loaded")
        self.assertIn("fleet-math", shell.loaded_racks)

    def test_load_rack_unknown(self):
        shell = self.state.create_shell("agent-1", "Test")
        result = self.state.load_rack(shell.session_id, "nonexistent")
        self.assertIn("error", result)

    def test_load_rack_duplicate(self):
        shell = self.state.create_shell("agent-1", "Test")
        self.state.load_rack(shell.session_id, "fleet-math")
        result = self.state.load_rack(shell.session_id, "fleet-math")
        self.assertEqual(result["status"], "already_loaded")

    def test_inject_skill(self):
        shell = self.state.create_shell("agent-1", "Test")
        result = self.state.inject_skill(shell.session_id, "eisenstein")
        self.assertEqual(result["status"], "injected")
        self.assertIn("eisenstein", shell.loaded_skills)
        self.assertIn("skill:eisenstein", shell.runtime_state)

    def test_inject_skill_unknown(self):
        shell = self.state.create_shell("agent-1", "Test")
        result = self.state.inject_skill(shell.session_id, "telekinesis")
        self.assertIn("error", result)

    def test_get_status(self):
        status = self.state.get_status()
        self.assertEqual(status["status"], "ok")
        self.assertIn("available_racks", status)
        self.assertIn("available_skills", status)


class TestDojo(unittest.TestCase):
    """Test dojo training scenarios."""

    def setUp(self):
        self.dojo = Dojo(scenarios_dir=str(BASE_DIR / "dojo" / "scenarios"))

    def test_list_scenarios(self):
        scenarios = self.dojo.list_scenarios()
        self.assertIn("drift-detect", scenarios)
        self.assertIn("adversarial", scenarios)

    def test_start_scenario(self):
        session = self.dojo.start("drift-detect", agent_id="neo")
        self.assertEqual(session.scenario, "drift-detect")
        self.assertFalse(session.answered)

    def test_submit_correct_answer(self):
        session = self.dojo.start("drift-detect", agent_id="neo")
        result = self.dojo.submit(session.session_id, "Between indices 4 and 5")
        self.assertTrue(result["correct"])
        self.assertGreater(result["score"], 0)

    def test_submit_wrong_answer(self):
        session = self.dojo.start("drift-detect", agent_id="neo")
        result = self.dojo.submit(session.session_id, "No drift detected")
        self.assertFalse(result["correct"])

    def test_submit_twice(self):
        session = self.dojo.start("drift-detect", agent_id="neo")
        self.dojo.submit(session.session_id, "Between indices 4 and 5")
        result = self.dojo.submit(session.session_id, "Between indices 2 and 3")
        self.assertIn("error", result)

    def test_adversarial_scenario(self):
        session = self.dojo.start("adversarial", agent_id="neo")
        result = self.dojo.submit(session.session_id, "Agent B")
        self.assertTrue(result["correct"])


class TestDojoScoring(unittest.TestCase):
    """Test scoring engine."""

    def test_record_result(self):
        scoring = DojoScoring()
        score = scoring.record_result("neo", "drift-detect", True, 120, 120, 3.5, "medium")
        self.assertEqual(score.scenarios_completed, 1)
        self.assertEqual(score.correct_count, 1)
        self.assertEqual(score.accuracy, 1.0)

    def test_badge_awarded(self):
        scoring = DojoScoring()
        scoring.record_result("neo", "drift-detect", True, 120, 120, 3.5, "medium")
        score = scoring.get_score("neo")
        self.assertTrue(any("First Steps" in b for b in score.badges))

    def test_leaderboard(self):
        scoring = DojoScoring()
        scoring.record_result("neo", "drift-detect", True, 120, 120, 3.5, "medium")
        scoring.record_result("trinity", "drift-detect", True, 80, 120, 10.0, "medium")
        lb = scoring.leaderboard()
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[0]["agent_id"], "neo")  # higher score first


class TestHolodeck(unittest.TestCase):
    """Test holodeck programs."""

    def setUp(self):
        self.holodeck = Holodeck(programs_dir=str(BASE_DIR / "holodeck" / "programs"))

    def test_list_programs(self):
        programs = self.holodeck.list_programs()
        self.assertIn("flight", programs)
        self.assertIn("combat", programs)
        self.assertIn("medical", programs)
        self.assertIn("engineering", programs)

    def test_load_program(self):
        result = self.holodeck.load("agent-1", "flight")
        self.assertEqual(result["status"], "loaded")
        self.assertEqual(result["program"], "flight")

    def test_unload_program(self):
        self.holodeck.load("agent-1", "flight")
        result = self.holodeck.unload("agent-1")
        self.assertEqual(result["status"], "unloaded")
        self.assertEqual(result["removed"], "flight")

    def test_context_tiles(self):
        tiles = self.holodeck.get_context_tiles("flight")
        self.assertGreater(len(tiles), 0)
        self.assertTrue(all("holodeck" in t["tags"] for t in tiles))

    def test_load_nonexistent(self):
        result = self.holodeck.load("agent-1", "telekinesis")
        self.assertIn("error", result)


class TestContextSwap(unittest.TestCase):
    """Test context window swap."""

    def test_swap_in(self):
        swap = ContextSwap()
        result = swap.swap_in("agent-1", "flight",
                              current_tiles=[{"room": "base"}],
                              current_runtime={"x": 1},
                              program_tiles=[{"room": "flight"}])
        self.assertEqual(result["status"], "swapped_in")
        self.assertEqual(result["program"], "flight")

    def test_swap_out(self):
        swap = ContextSwap()
        swap.swap_in("agent-1", "flight",
                     current_tiles=[], current_runtime={},
                     program_tiles=[])
        result = swap.swap_out("agent-1")
        self.assertEqual(result["status"], "swapped_out")
        self.assertEqual(result["removed_program"], "flight")

    def test_swap_stack(self):
        swap = ContextSwap()
        swap.swap_in("agent-1", "flight", [], {}, [])
        swap.swap_in("agent-1", "combat", [], {}, [])
        self.assertEqual(swap.get_stack_depth("agent-1"), 2)
        swap.swap_out("agent-1")
        self.assertEqual(swap.get_stack_depth("agent-1"), 1)
        self.assertEqual(swap.get_active_program("agent-1"), "flight")


class TestSkills(unittest.TestCase):
    """Test skill modules are importable."""

    def test_eisenstein_skill(self):
        eis = _import_from_path("eisenstein", BASE_DIR / "skills" / "eisenstein.py")
        self.assertEqual(eis.eisenstein_norm(3, 2), 7)  # 9 - 6 + 4 = 7
        self.assertEqual(eis.eisenstein_norm(5, -3), 49)  # 25 + 15 + 9 = 49

    def test_hebbian_skill(self):
        heb = _import_from_path("hebbian", BASE_DIR / "skills" / "hebbian.py")
        m = heb.HebbianMatrix()
        m.activate("room-a")
        m.activate("room-b")
        w = m.get_weight("room-a", "room-b")
        self.assertGreater(w, 0.0)

    def test_conservation_skill(self):
        cons = _import_from_path("conservation", BASE_DIR / "skills" / "conservation.py")
        state = cons.check_conservation([0.5, 0.3, 0.2], volume=5)
        self.assertIn("gamma", state.to_dict())
        self.assertIn("is_compliant", dir(state))

    def test_translation_skill(self):
        trans = _import_from_path("translation", BASE_DIR / "skills" / "translation.py")
        hit = trans.detect_vocabulary_wall("Compute the Eisenstein norm of a=3, b=5")
        self.assertIsNotNone(hit)
        self.assertIn("eisenstein", [t.lower() for t in hit.blocked_terms])

    def test_fault_detect_skill(self):
        fault = _import_from_path("fault_detect", BASE_DIR / "skills" / "fault-detect.py")
        report = fault.detect_faults(
            "test-agent",
            [{"confidence": 0.5}, {"confidence": 0.5}],
            [0.5, 0.3, 0.2],
            volume=3,
        )
        self.assertIn(report.level, [fault.FaultLevel.NONE, fault.FaultLevel.MONITOR])


class TestConfig(unittest.TestCase):
    """Test configuration loading."""

    def test_default_config(self):
        config = load_config()
        self.assertIn("server", config)
        self.assertEqual(config["server"]["port"], 8849)

    def test_construct_json_exists(self):
        path = BASE_DIR / "construct.json"
        self.assertTrue(path.exists())
        data = json.loads(path.read_text())
        self.assertIn("rack_manifest", data)
        self.assertIn("skill_manifest", data)


class TestIntegration(unittest.TestCase):
    """Integration test: full agent workflow."""

    def test_full_workflow(self):
        """Simulate: enter → load rack → inject skill → train → holodeck → exit."""
        config = load_config(str(BASE_DIR / "construct.json"))
        state = ConstructState(config)

        # Enter
        shell = state.create_shell("neo", "Neo")
        self.assertTrue(shell.session_id)

        # Load rack
        result = state.load_rack(shell.session_id, "fleet-math")
        self.assertEqual(result["status"], "loaded")
        self.assertGreater(len(shell.tiles), 0)

        # Inject skill
        result = state.inject_skill(shell.session_id, "eisenstein")
        self.assertEqual(result["status"], "injected")

        # Start training
        result = state.start_training(shell.session_id, "adversarial")
        self.assertEqual(result["status"], "training_started")

        # Submit answer
        result = state.submit_training_answer(shell.session_id, "Agent B")
        self.assertTrue(result["correct"])

        # Load holodeck
        result = state.load_holodeck(shell.session_id, "flight")
        self.assertEqual(result["status"], "loaded")
        self.assertIn("flight", shell.context_program)

        # Unload holodeck
        result = state.unload_holodeck(shell.session_id)
        self.assertEqual(result["status"], "unloaded")

        # Exit
        removed = state.remove_shell(shell.session_id)
        self.assertEqual(removed.agent_id, "neo")
        self.assertIsNone(state.get_shell(shell.session_id))


if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  The Construct — Test Suite")
    print(f"  Running from: {BASE_DIR}")
    print(f"{'='*60}\n")
    unittest.main(verbosity=2)
