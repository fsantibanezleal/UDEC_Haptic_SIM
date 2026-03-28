"""
Tests for the spring force model and surface proximity queries.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.physics import (
    SpringForceModel,
    find_nearest_surface_point,
    closest_point_on_triangle,
)
from app.simulation.obj_loader import create_box, create_sphere


def test_spring_no_contact():
    """No anchor means zero force."""
    model = SpringForceModel(stiffness=1.0)
    force = model.compute_force(np.array([1, 0, 0.0]))
    assert np.allclose(force, [0, 0, 0]), "Should be zero without contact"
    print("  [PASS] Zero force without contact")


def test_spring_basic_force():
    """Force should oppose displacement from anchor."""
    model = SpringForceModel(stiffness=1.0, damping=0.0, max_force=10.0)
    model.set_anchor(np.array([0, 0, 0.0]))
    force = model.compute_force(np.array([1, 0, 0.0]))
    assert force[0] < 0, "Force should push probe back toward anchor"
    assert np.isclose(force[0], -1.0), f"Expected -1.0, got {force[0]}"
    print("  [PASS] Basic spring force")


def test_spring_damping():
    """Damping should reduce force when moving away from anchor."""
    model = SpringForceModel(stiffness=1.0, damping=0.5, max_force=10.0)
    model.set_anchor(np.array([0, 0, 0.0]))
    force = model.compute_force(
        np.array([1, 0, 0.0]),
        probe_velocity=np.array([1, 0, 0.0]),
    )
    # F = -1*1 - 0.5*1 = -1.5 in x
    assert np.isclose(force[0], -1.5), f"Expected -1.5, got {force[0]}"
    print("  [PASS] Damping force")


def test_spring_force_clamping():
    """Force magnitude should be clamped to max_force."""
    model = SpringForceModel(stiffness=10.0, damping=0.0, max_force=3.3)
    model.set_anchor(np.array([0, 0, 0.0]))
    force = model.compute_force(np.array([5, 0, 0.0]))
    mag = np.linalg.norm(force)
    assert mag <= 3.3 + 1e-6, f"Force {mag} exceeds max 3.3"
    print(f"  [PASS] Force clamping (|F| = {mag:.3f})")


def test_spring_release():
    """After release, force should be zero."""
    model = SpringForceModel(stiffness=1.0)
    model.set_anchor(np.array([0, 0, 0.0]))
    model.release()
    force = model.compute_force(np.array([1, 0, 0.0]))
    assert np.allclose(force, [0, 0, 0]), "Should be zero after release"
    print("  [PASS] Force zero after release")


def test_closest_point_on_triangle_interior():
    """Point directly above triangle centre should project to centre."""
    a = np.array([0, 0, 0.0])
    b = np.array([1, 0, 0.0])
    c = np.array([0, 1, 0.0])
    p = np.array([0.25, 0.25, 5.0])

    result = closest_point_on_triangle(p, a, b, c)
    assert np.isclose(result[2], 0.0), "Z should be 0 (on triangle plane)"
    assert np.isclose(result[0], 0.25) and np.isclose(result[1], 0.25)
    print("  [PASS] Closest point interior projection")


def test_closest_point_on_triangle_vertex():
    """Point near vertex A should project to A."""
    a = np.array([0, 0, 0.0])
    b = np.array([1, 0, 0.0])
    c = np.array([0, 1, 0.0])
    p = np.array([-1, -1, 0.0])

    result = closest_point_on_triangle(p, a, b, c)
    assert np.allclose(result, a), f"Expected vertex A, got {result}"
    print("  [PASS] Closest point vertex projection")


def test_find_nearest_surface():
    """Nearest surface point on a box should be on a face."""
    box = create_box(np.array([0, 0, 0.0]), size=2.0)
    probe = np.array([0, 0, 3.0])
    pt, fi, dist = find_nearest_surface_point(probe, box)
    assert dist < 3.0, f"Distance {dist} seems too large"
    assert fi >= 0, "Face index should be valid"
    print(f"  [PASS] Nearest surface (dist={dist:.3f}, face={fi})")


def test_friction_zero_by_default():
    """Friction coefficient should default to zero."""
    model = SpringForceModel(stiffness=1.0)
    assert model.friction_coefficient == 0.0
    print("  [PASS] Friction zero by default")


def test_friction_in_state():
    """Friction coefficient should appear in serialized state."""
    model = SpringForceModel(stiffness=1.0, friction_coefficient=0.3)
    state = model.get_state()
    assert 'friction_coefficient' in state
    assert state['friction_coefficient'] == 0.3
    print("  [PASS] Friction in state")


def test_friction_opposes_tangential_motion():
    """Friction should oppose tangential velocity component."""
    model = SpringForceModel(stiffness=1.0, damping=0.0, max_force=100.0,
                              friction_coefficient=0.5)
    model.set_anchor(np.array([0, 0, 0.0]))
    # Probe displaced along x, moving along y (tangential)
    force = model.compute_force(
        np.array([1.0, 0.0, 0.0]),
        probe_velocity=np.array([0.0, 1.0, 0.0]),
    )
    # Spring force is -1.0 in x direction
    # Friction should oppose y-velocity: negative y component
    assert force[1] < 0, f"Friction should oppose tangential motion, got Fy={force[1]}"
    print(f"  [PASS] Friction opposes tangential motion (Fy={force[1]:.4f})")


def test_friction_no_effect_without_velocity():
    """Friction should have no effect when no velocity is provided."""
    model = SpringForceModel(stiffness=1.0, damping=0.0, max_force=10.0,
                              friction_coefficient=0.5)
    model.set_anchor(np.array([0, 0, 0.0]))
    force_no_v = model.compute_force(np.array([1.0, 0.0, 0.0]))
    force_zero_v = model.compute_force(
        np.array([1.0, 0.0, 0.0]),
        probe_velocity=np.array([0.0, 0.0, 0.0]),
    )
    # Without velocity, both should give the same spring force
    assert np.allclose(force_no_v, force_zero_v), \
        "Friction should have no effect without velocity"
    print("  [PASS] Friction no effect without velocity")


def test_friction_increases_total_force():
    """Friction should add to total force magnitude for tangential motion."""
    model_no_friction = SpringForceModel(stiffness=1.0, damping=0.0, max_force=100.0,
                                          friction_coefficient=0.0)
    model_friction = SpringForceModel(stiffness=1.0, damping=0.0, max_force=100.0,
                                       friction_coefficient=0.5)
    model_no_friction.set_anchor(np.array([0, 0, 0.0]))
    model_friction.set_anchor(np.array([0, 0, 0.0]))

    pos = np.array([1.0, 0.0, 0.0])
    vel = np.array([0.0, 2.0, 0.0])  # tangential velocity

    f1 = model_no_friction.compute_force(pos, vel)
    f2 = model_friction.compute_force(pos, vel)

    mag1 = np.linalg.norm(f1)
    mag2 = np.linalg.norm(f2)
    assert mag2 > mag1, f"Friction should increase force: {mag2} vs {mag1}"
    print(f"  [PASS] Friction increases total force ({mag2:.4f} > {mag1:.4f})")


if __name__ == "__main__":
    print("=== Physics Tests ===")
    test_spring_no_contact()
    test_spring_basic_force()
    test_spring_damping()
    test_spring_force_clamping()
    test_spring_release()
    test_closest_point_on_triangle_interior()
    test_closest_point_on_triangle_vertex()
    test_find_nearest_surface()
    test_friction_zero_by_default()
    test_friction_in_state()
    test_friction_opposes_tangential_motion()
    test_friction_no_effect_without_velocity()
    test_friction_increases_total_force()
    print("=== All physics tests passed ===")
