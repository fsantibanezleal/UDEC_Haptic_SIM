"""
Tests for the Scene manager.

Note: Collision detection has been moved to the Three.js frontend
for performance. The backend Scene.step() handles force computation
and body state. Collision tests remain in test_collision.py.
"""
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.scene import Scene
from app.simulation.obj_loader import create_box, create_sphere


def test_default_scene():
    """Default scene should load with 3 bodies."""
    scene = Scene()
    scene.load_default_scene()
    assert len(scene.bodies) == 3
    names = [b.name for b in scene.bodies]
    assert "Cube A" in names
    assert "Cube B" in names
    assert "Sphere" in names
    print("  [PASS] Default scene loads 3 bodies")


def test_scene_step():
    """A simulation step should return valid state dict."""
    scene = Scene()
    scene.load_default_scene()
    state = scene.step()
    assert "bodies" in state
    assert "probe" in state
    assert "force" in state
    assert len(state["bodies"]) == 3
    print("  [PASS] Scene step returns valid state")


def test_scene_force_with_anchor():
    """Setting an anchor near the probe should produce force."""
    scene = Scene()
    scene.load_default_scene()
    scene.set_probe_position(np.array([0.0, 0.0, 0.5]))
    scene.force_model.set_anchor(np.array([0.0, 0.0, 0.0]))
    state = scene.step()
    mag = state["force"]["magnitude"]
    assert mag > 0, f"Expected force > 0, got {mag}"
    print(f"  [PASS] Force with anchor (|F| = {mag:.4f})")


def test_scene_no_force_no_anchor():
    """Without anchor, force should be zero."""
    scene = Scene()
    scene.load_default_scene()
    scene.force_model.release()
    state = scene.step()
    assert state["force"]["magnitude"] == 0.0
    print("  [PASS] No force without anchor")


def test_scene_add_remove():
    """Adding and removing bodies should work."""
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]))
    idx = scene.add_body(box)
    assert len(scene.bodies) == 1
    scene.remove_body(idx)
    assert len(scene.bodies) == 0
    print("  [PASS] Add/remove body")


def test_scene_clear():
    """Clear should remove all bodies."""
    scene = Scene()
    scene.load_default_scene()
    scene.clear()
    assert len(scene.bodies) == 0
    print("  [PASS] Scene clear")


def test_scene_serialization():
    """State serialization should produce valid JSON."""
    scene = Scene()
    scene.load_default_scene()
    state = scene.step()
    json_str = json.dumps(state)
    assert len(json_str) > 100
    parsed = json.loads(json_str)
    assert len(parsed["bodies"]) == 3
    print(f"  [PASS] Serialization ({len(json_str)} chars)")


def test_body_transform():
    """Transforming a body should update its vertices."""
    scene = Scene()
    scene.load_default_scene()
    old_pos = scene.bodies[0].position.copy()
    scene.bodies[0].translate(np.array([1.0, 0.0, 0.0]))
    new_pos = scene.bodies[0].position
    assert new_pos[0] > old_pos[0] + 0.9
    print("  [PASS] Body transform updates position")


if __name__ == "__main__":
    print("=== Scene Tests ===")
    test_default_scene()
    test_scene_step()
    test_scene_force_with_anchor()
    test_scene_no_force_no_anchor()
    test_scene_add_remove()
    test_scene_clear()
    test_scene_serialization()
    test_body_transform()
    print("=== All scene tests passed ===")
