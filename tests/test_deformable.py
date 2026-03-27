"""
Tests for deformable body physics.

Tests spring network construction, MSD integration,
XPBD constraint solving, floor collisions, and force application.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.deformable import DeformableBody
from app.simulation.obj_loader import create_box, create_sphere


def test_spring_network_from_box():
    """A box has 12 unique edges (structural springs)."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box)
    # A cube has 12 edges, but triangulated cube faces create extra edges
    # 6 faces * 2 triangles each, each triangle has 3 edges
    # Unique edges: 12 original + 6 diagonal = 18
    assert len(deformable.springs) == 18, \
        f"Expected 18 unique edges for a triangulated box, got {len(deformable.springs)}"
    assert len(deformable.spring_rest_lengths) == len(deformable.springs)
    assert np.all(deformable.spring_rest_lengths > 0)
    print(f"  [PASS] Spring network from box ({len(deformable.springs)} springs)")


def test_msd_gravity():
    """Under gravity, vertices should move downward."""
    box = create_box(np.array([0, 2, 0.0]), size=0.5)
    deformable = DeformableBody.from_rigid_body(box, stiffness=500, damping=5)
    initial_y = deformable.vertices[:, 1].mean()

    for _ in range(10):
        deformable.step_msd(dt=1/60, gravity=-9.81, floor_y=-10.0)

    final_y = deformable.vertices[:, 1].mean()
    assert final_y < initial_y, \
        f"Vertices should move down: {initial_y:.3f} -> {final_y:.3f}"
    print(f"  [PASS] MSD gravity (y: {initial_y:.3f} -> {final_y:.3f})")


def test_msd_spring_restoring():
    """A stretched spring should restore toward rest length."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box, stiffness=1000, damping=10)

    # Stretch the first vertex outward
    deformable.vertices[0] += np.array([0.5, 0.0, 0.0])
    initial_offset = np.linalg.norm(deformable.vertices[0] - deformable.rest_vertices[0])

    for _ in range(50):
        deformable.step_msd(dt=1/60, gravity=0.0, floor_y=-100.0)

    final_offset = np.linalg.norm(deformable.vertices[0] - deformable.rest_vertices[0])
    # Spring force should pull vertex back (though not necessarily to exact rest)
    assert final_offset < initial_offset, \
        f"Spring should restore: {initial_offset:.3f} -> {final_offset:.3f}"
    print(f"  [PASS] MSD spring restoring ({initial_offset:.3f} -> {final_offset:.3f})")


def test_xpbd_distance_constraint():
    """XPBD should approximately preserve edge lengths under gravity."""
    box = create_box(np.array([0, 2, 0.0]), size=0.5)
    deformable = DeformableBody.from_rigid_body(box, solver="xpbd", stiffness=10000)
    original_lengths = deformable.spring_rest_lengths.copy()

    for _ in range(30):
        deformable.step_xpbd(dt=1/60, iterations=10, gravity=-9.81, floor_y=-10.0)

    # Compute current edge lengths
    current_lengths = np.linalg.norm(
        deformable.vertices[deformable.springs[:, 1]] -
        deformable.vertices[deformable.springs[:, 0]],
        axis=1,
    )

    relative_error = np.abs(current_lengths - original_lengths) / original_lengths
    max_error = relative_error.max()
    assert max_error < 0.5, f"XPBD max relative length error {max_error:.3f} too large"
    print(f"  [PASS] XPBD distance constraint (max_error={max_error:.3f})")


def test_floor_collision():
    """Vertices should not go below the floor."""
    box = create_box(np.array([0, -1.0, 0.0]), size=0.5)
    deformable = DeformableBody.from_rigid_body(box, stiffness=500)
    floor_y = -1.5

    for _ in range(30):
        deformable.step_msd(dt=1/60, gravity=-9.81, floor_y=floor_y)

    min_y = deformable.vertices[:, 1].min()
    assert min_y >= floor_y - 0.001, \
        f"Vertices should not go below floor: min_y={min_y:.3f}, floor={floor_y}"
    print(f"  [PASS] Floor collision (min_y={min_y:.3f}, floor={floor_y})")


def test_apply_force_at_point():
    """Applying force at a point should affect nearby vertices."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box, stiffness=500)
    initial_vels = deformable.velocities.copy()

    point = np.array([0.5, 0.5, 0.5])  # near a corner
    force = np.array([10.0, 0.0, 0.0])
    deformable.apply_force_at_point(point, force, radius=0.5)

    # At least some velocities should have changed
    vel_diff = np.linalg.norm(deformable.velocities - initial_vels, axis=1)
    assert np.any(vel_diff > 0.0), "Force should affect nearby vertices"
    print(f"  [PASS] Apply force at point ({np.sum(vel_diff > 0)} vertices affected)")


def test_from_rigid_body():
    """Converting RigidBody to DeformableBody should preserve geometry."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box)
    assert deformable.body_type == "deformable"
    assert np.allclose(deformable.vertices, box.vertices)
    assert np.array_equal(deformable.faces, box.faces)
    print("  [PASS] From rigid body conversion")


def test_deformable_get_state():
    """get_state should include body_type and solver."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box, solver="xpbd")
    state = deformable.get_state()
    assert state["body_type"] == "deformable"
    assert state["solver"] == "xpbd"
    assert "spring_count" in state
    print("  [PASS] Deformable get_state")


if __name__ == "__main__":
    print("=== Deformable Body Tests ===")
    test_spring_network_from_box()
    test_msd_gravity()
    test_msd_spring_restoring()
    test_xpbd_distance_constraint()
    test_floor_collision()
    test_apply_force_at_point()
    test_from_rigid_body()
    test_deformable_get_state()
    print("=== All deformable tests passed ===")
