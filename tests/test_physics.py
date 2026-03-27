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
    print("=== All physics tests passed ===")
