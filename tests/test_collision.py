"""
Tests for hierarchical collision detection.

Tests the vectorized AABB-based collision pipeline:
    Level 1: Body AABB broad phase
    Level 2: Triangle AABB batch filter (NumPy broadcast)
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.collision import (
    AABB,
    detect_all_collisions,
    find_nearest_surface_vectorized,
    precompute_collision_data,
    body_aabb_overlaps,
    find_triangle_collisions,
    _closest_point_on_triangle,
)
from app.simulation.obj_loader import create_box, create_sphere


def test_aabb_intersection():
    """AABBs that overlap should report True."""
    a = AABB(np.array([0, 0, 0.0]), np.array([1, 1, 1.0]))
    b = AABB(np.array([0.5, 0.5, 0.5]), np.array([1.5, 1.5, 1.5]))
    assert a.intersects(b)
    c = AABB(np.array([2, 2, 2.0]), np.array([3, 3, 3.0]))
    assert not a.intersects(c)
    print("  [PASS] AABB intersection")


def test_precompute_collision_data():
    """Pre-computed data should have correct shapes."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    data = precompute_collision_data(box, 0)
    assert data.tri_aabb_min.shape == (12, 3)  # 12 faces for a box
    assert data.tri_centroids.shape == (12, 3)
    assert data.tri_v0.shape == (12, 3)
    print("  [PASS] Pre-compute collision data")


def test_body_broad_phase_overlap():
    """Overlapping bodies should be detected."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([0.5, 0, 0.0]), size=1.0)
    da = precompute_collision_data(a, 0)
    db = precompute_collision_data(b, 1)
    pairs = body_aabb_overlaps([da, db])
    assert len(pairs) == 1
    print("  [PASS] Body broad phase (overlap)")


def test_body_broad_phase_separated():
    """Separated bodies should NOT be detected."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([5, 0, 0.0]), size=1.0)
    da = precompute_collision_data(a, 0)
    db = precompute_collision_data(b, 1)
    pairs = body_aabb_overlaps([da, db])
    assert len(pairs) == 0
    print("  [PASS] Body broad phase (separated)")


def test_triangle_batch_filter():
    """Vectorized triangle AABB filter should find overlapping faces."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([0.5, 0, 0.0]), size=1.0)
    da = precompute_collision_data(a, 0)
    db = precompute_collision_data(b, 1)
    pairs = find_triangle_collisions(da, db)
    assert len(pairs) > 0, "Overlapping boxes should have triangle collisions"
    print(f"  [PASS] Triangle batch filter ({len(pairs)} pairs)")


def test_full_pipeline_overlapping():
    """Full pipeline should detect collisions between overlapping bodies."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([0.5, 0, 0.0]), size=1.0)
    data, pairs = detect_all_collisions([a, b])
    assert len(data) == 2
    assert len(pairs) > 0
    print(f"  [PASS] Full pipeline overlapping ({len(pairs)} collisions)")


def test_full_pipeline_separated():
    """Full pipeline should find zero collisions for separated bodies."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([5, 0, 0.0]), size=1.0)
    _, pairs = detect_all_collisions([a, b])
    assert len(pairs) == 0
    print("  [PASS] Full pipeline separated (0 collisions)")


def test_nearest_surface():
    """Nearest surface should find a close point."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    data = [precompute_collision_data(box, 0)]
    probe = np.array([0.0, 0.0, 0.6])
    pt, dist = find_nearest_surface_vectorized(probe, data, top_k=5)
    assert dist < 0.2, f"Expected close distance, got {dist}"
    print(f"  [PASS] Nearest surface (dist={dist:.3f})")


def test_closest_point_on_triangle():
    """Closest point projection should work for various cases."""
    a = np.array([0, 0, 0.0])
    b = np.array([1, 0, 0.0])
    c = np.array([0, 1, 0.0])
    # Point above triangle interior
    p = np.array([0.2, 0.2, 1.0])
    pt = _closest_point_on_triangle(p, a, b, c)
    assert abs(pt[2]) < 1e-10, "Projected point should be on the triangle plane"
    print("  [PASS] Closest point on triangle")


if __name__ == "__main__":
    print("=== Collision Detection Tests ===")
    test_aabb_intersection()
    test_precompute_collision_data()
    test_body_broad_phase_overlap()
    test_body_broad_phase_separated()
    test_triangle_batch_filter()
    test_full_pipeline_overlapping()
    test_full_pipeline_separated()
    test_nearest_surface()
    test_closest_point_on_triangle()
    print("=== All collision tests passed ===")
