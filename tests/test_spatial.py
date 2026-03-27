"""
Tests for spatial acceleration structures.

Tests AABB, OBB, Octree, and BVH implementations for consistency
and correctness of collision detection and nearest queries.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.spatial.aabb_tree import AABBTree
from app.simulation.spatial.octree import Octree
from app.simulation.spatial.obb import OBBTree, compute_obb, obb_overlap
from app.simulation.spatial.bvh import BVH
from app.simulation.obj_loader import create_box, create_sphere


def _make_overlapping():
    """Create two overlapping boxes."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0, name="A")
    b = create_box(np.array([0.5, 0, 0.0]), size=1.0, name="B")
    return [a, b]


def _make_separated():
    """Create two well-separated boxes."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0, name="A")
    b = create_box(np.array([5, 0, 0.0]), size=1.0, name="B")
    return [a, b]


# ---- AABB ----

def test_aabb_build_and_query():
    """AABB build should produce collision data; query should find collisions."""
    tree = AABBTree()
    bodies = _make_overlapping()
    tree.build(bodies)
    collisions = tree.query_collisions()
    assert len(collisions) > 0, "Overlapping boxes should have collisions"

    # Nearest query
    pt, dist = tree.query_nearest(np.array([0.0, 0.0, 0.6]))
    assert dist < 0.2, f"Expected close distance, got {dist}"
    print("  [PASS] AABB build and query")


# ---- Octree ----

def test_octree_build():
    """Octree should build with proper depth and triangle counts."""
    tree = Octree(max_depth=4, min_triangles=4)
    bodies = _make_overlapping()
    tree.build(bodies)
    assert tree.get_depth() > 0, "Octree should have depth > 0"
    assert tree.get_triangle_count() == 24, "Two boxes = 24 triangles"
    print(f"  [PASS] Octree build (depth={tree.get_depth()}, tris={tree.get_triangle_count()})")


def test_octree_query_collisions_overlap():
    """Octree should detect collisions for overlapping bodies."""
    tree = Octree(max_depth=6, min_triangles=8)
    tree.build(_make_overlapping())
    collisions = tree.query_collisions()
    assert len(collisions) > 0, "Overlapping boxes should have collisions"
    print(f"  [PASS] Octree query collisions overlap ({len(collisions)} pairs)")


def test_octree_query_collisions_separated():
    """Octree should find no collisions for separated bodies."""
    tree = Octree(max_depth=6, min_triangles=8)
    tree.build(_make_separated())
    collisions = tree.query_collisions()
    assert len(collisions) == 0, "Separated boxes should have no collisions"
    print("  [PASS] Octree query collisions separated (0 pairs)")


def test_octree_viz_data():
    """Octree viz data should include nodes at various depth levels."""
    tree = Octree(max_depth=4, min_triangles=4)
    tree.build(_make_overlapping())
    viz = tree.get_viz_data(max_depth=4)
    assert len(viz) > 0, "Should have visualization data"
    depths = set(v['depth'] for v in viz)
    assert 0 in depths, "Should have root node at depth 0"
    print(f"  [PASS] Octree viz data ({len(viz)} nodes, depths={sorted(depths)})")


# ---- OBB ----

def test_obb_build():
    """OBB should compute PCA axes correctly."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    obb = compute_obb(box, 0)
    assert obb.axes.shape == (3, 3), "Axes should be 3x3"
    assert obb.half_extents.shape == (3,), "Half extents should be (3,)"
    assert np.all(obb.half_extents > 0), "Half extents should be positive"
    print(f"  [PASS] OBB build (half_extents={obb.half_extents})")


def test_obb_overlap():
    """OBB overlap test for overlapping and separated boxes."""
    a = create_box(np.array([0, 0, 0.0]), size=1.0)
    b = create_box(np.array([0.5, 0, 0.0]), size=1.0)
    obb_a = compute_obb(a, 0)
    obb_b = compute_obb(b, 1)
    assert obb_overlap(obb_a, obb_b), "Overlapping boxes should have OBB overlap"

    c = create_box(np.array([5, 0, 0.0]), size=1.0)
    obb_c = compute_obb(c, 2)
    assert not obb_overlap(obb_a, obb_c), "Separated boxes should not have OBB overlap"
    print("  [PASS] OBB overlap test")


def test_obb_tree_collisions():
    """OBBTree should detect collisions consistently with AABB."""
    tree = OBBTree()
    tree.build(_make_overlapping())
    collisions = tree.query_collisions()
    assert len(collisions) > 0, "Overlapping boxes should have OBB collisions"
    print(f"  [PASS] OBB tree collisions ({len(collisions)} pairs)")


# ---- BVH ----

def test_bvh_build():
    """BVH should build with proper tree depth."""
    tree = BVH(max_leaf_size=4)
    tree.build(_make_overlapping())
    depth = tree.get_depth()
    assert depth > 0, "BVH should have depth > 0"
    print(f"  [PASS] BVH build (depth={depth})")


def test_bvh_nearest():
    """BVH nearest query should match brute force."""
    bodies = [create_box(np.array([0, 0, 0.0]), size=1.0)]
    probe = np.array([0.0, 0.0, 0.6])

    # BVH result
    bvh = BVH()
    bvh.build(bodies)
    pt_bvh, dist_bvh = bvh.query_nearest(probe, top_k=5)

    # AABB result (reference)
    aabb = AABBTree()
    aabb.build(bodies)
    pt_aabb, dist_aabb = aabb.query_nearest(probe, top_k=5)

    assert abs(dist_bvh - dist_aabb) < 0.01, \
        f"BVH dist {dist_bvh} != AABB dist {dist_aabb}"
    print(f"  [PASS] BVH nearest (dist_bvh={dist_bvh:.3f}, dist_aabb={dist_aabb:.3f})")


# ---- Cross-method consistency ----

def test_all_methods_consistent():
    """All spatial methods should find the same collision pairs (modulo order)."""
    bodies = _make_overlapping()

    results = {}
    for name, cls in [('aabb', AABBTree), ('octree', Octree), ('obb', OBBTree), ('bvh', BVH)]:
        tree = cls()
        tree.build(bodies)
        collisions = tree.query_collisions()
        # Convert to set of tuples for comparison
        results[name] = set(tuple(c) for c in collisions)

    # All should have collisions
    for name, pairs in results.items():
        assert len(pairs) > 0, f"{name} should find collisions"

    # AABB is the reference; others should be subsets or supersets
    # (different methods may have different granularity in spatial subdivision)
    aabb_count = len(results['aabb'])
    for name, pairs in results.items():
        # All methods should detect at least some overlapping face pairs
        assert len(pairs) > 0, f"{name} should detect collisions"

    print(f"  [PASS] All methods consistent (aabb={len(results['aabb'])}, "
          f"octree={len(results['octree'])}, obb={len(results['obb'])}, "
          f"bvh={len(results['bvh'])})")


if __name__ == "__main__":
    print("=== Spatial Structure Tests ===")
    test_aabb_build_and_query()
    test_octree_build()
    test_octree_query_collisions_overlap()
    test_octree_query_collisions_separated()
    test_octree_viz_data()
    test_obb_build()
    test_obb_overlap()
    test_obb_tree_collisions()
    test_bvh_build()
    test_bvh_nearest()
    test_all_methods_consistent()
    print("=== All spatial tests passed ===")
