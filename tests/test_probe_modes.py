"""
Tests for probe interaction modes.

Tests free, grab, and push modes and mode transitions.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.probe_modes import ProbeController
from app.simulation.scene import Scene
from app.simulation.obj_loader import create_box
from app.simulation.deformable import DeformableBody


def test_free_mode_default():
    """Default mode should be 'free'."""
    controller = ProbeController()
    assert controller.mode == "free"
    assert controller.grabbed_body_index is None
    print("  [PASS] Free mode default")


def test_grab_mode():
    """In grab mode, body should follow probe movement."""
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=1.0, name="Box")
    scene.add_body(box)

    # Set probe near the body
    scene.probe_position = np.array([0.0, 0.0, 0.0])

    # Switch to grab mode
    scene.probe_controller.set_mode("grab", scene)
    assert scene.probe_controller.mode == "grab"
    assert scene.probe_controller.grabbed_body_index is not None

    # Move probe
    old_pos = scene.bodies[0].position.copy()
    scene.probe_position = np.array([1.0, 0.0, 0.0])
    scene.probe_controller.update(scene.probe_position, scene)

    new_pos = scene.bodies[0].position
    assert new_pos[0] > old_pos[0], \
        f"Body should follow probe: {old_pos} -> {new_pos}"
    print(f"  [PASS] Grab mode (body moved from {old_pos} to {new_pos})")


def test_push_mode():
    """In push mode, deformable vertices near probe should be displaced."""
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=1.0, name="Box")
    deformable = DeformableBody.from_rigid_body(box)
    scene.add_body(deformable)

    # Place probe near the body
    scene.probe_position = np.array([0.5, 0.0, 0.0])
    scene.probe_controller.set_mode("push", scene)
    scene.probe_controller.push_radius = 1.0
    scene.probe_controller.push_strength = 5.0

    initial_verts = deformable.vertices.copy()
    scene.probe_controller.update(scene.probe_position, scene)

    # Some vertices should have moved
    diff = np.linalg.norm(deformable.vertices - initial_verts, axis=1)
    assert np.any(diff > 0.0), "Push should displace nearby vertices"
    print(f"  [PASS] Push mode ({np.sum(diff > 0)} vertices displaced)")


def test_mode_transitions():
    """Switching between modes should work correctly."""
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    scene.add_body(box)
    scene.probe_position = np.array([0.0, 0.0, 0.0])

    controller = scene.probe_controller

    # Free -> Grab
    controller.set_mode("grab", scene)
    assert controller.mode == "grab"
    assert controller.grabbed_body_index is not None

    # Grab -> Push
    controller.set_mode("push", scene)
    assert controller.mode == "push"
    assert controller.grabbed_body_index is None

    # Push -> Free
    controller.set_mode("free", scene)
    assert controller.mode == "free"

    # Free -> Free (no-op)
    controller.set_mode("free", scene)
    assert controller.mode == "free"

    print("  [PASS] Mode transitions")


def test_grab_release_on_mode_change():
    """Switching from grab to another mode should release the grab."""
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    scene.add_body(box)
    scene.probe_position = np.array([0.0, 0.0, 0.0])

    controller = scene.probe_controller
    controller.set_mode("grab", scene)
    assert controller.grabbed_body_index is not None

    controller.set_mode("free", scene)
    assert controller.grabbed_body_index is None
    assert controller.grab_offset is None
    print("  [PASS] Grab release on mode change")


def test_get_state():
    """Probe controller state should include mode and settings."""
    controller = ProbeController()
    state = controller.get_state()
    assert "mode" in state
    assert "push_radius" in state
    assert "push_strength" in state
    assert state["mode"] == "free"
    print("  [PASS] Get state")


if __name__ == "__main__":
    print("=== Probe Modes Tests ===")
    test_free_mode_default()
    test_grab_mode()
    test_push_mode()
    test_mode_transitions()
    test_grab_release_on_mode_change()
    test_get_state()
    print("=== All probe mode tests passed ===")
