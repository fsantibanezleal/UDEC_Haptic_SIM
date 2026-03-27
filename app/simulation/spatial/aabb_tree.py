"""
AABB Tree spatial structure wrapping the existing vectorized collision pipeline.

Provides the SpatialStructure interface around the original hierarchical
AABB collision detection: body AABB broad phase, then triangle AABB
batch filter using NumPy broadcasting.

References:
    - Ericson (2004), Real-Time Collision Detection
"""
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from .base import SpatialStructure


@dataclass
class MeshCollisionData:
    """Pre-computed arrays for fast collision queries on a mesh.

    All arrays are computed once when a body is added or transformed,
    and reused across frames until the body moves again.
    """
    body_index: int
    body_aabb_min: np.ndarray       # (3,) body AABB min
    body_aabb_max: np.ndarray       # (3,) body AABB max
    tri_aabb_min: np.ndarray        # (F, 3) per-triangle AABB min
    tri_aabb_max: np.ndarray        # (F, 3) per-triangle AABB max
    tri_centroids: np.ndarray       # (F, 3) triangle centroids
    tri_v0: np.ndarray              # (F, 3) first vertex of each triangle
    tri_v1: np.ndarray              # (F, 3) second vertex
    tri_v2: np.ndarray              # (F, 3) third vertex


def precompute_collision_data(body, body_index: int) -> MeshCollisionData:
    """Build all acceleration structures for a body.

    Extracts triangle vertices, computes per-triangle AABBs and
    centroids in a single vectorized pass.

    Args:
        body: Body with vertices (N,3) and faces (F,3).
        body_index: Index of this body in the scene.

    Returns:
        MeshCollisionData with all pre-computed arrays.
    """
    verts = body.vertices
    faces = body.faces
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]

    stacked = np.stack([v0, v1, v2], axis=1)
    tri_min = stacked.min(axis=1)
    tri_max = stacked.max(axis=1)
    centroids = stacked.mean(axis=1)

    return MeshCollisionData(
        body_index=body_index,
        body_aabb_min=body.aabb_min.copy(),
        body_aabb_max=body.aabb_max.copy(),
        tri_aabb_min=tri_min,
        tri_aabb_max=tri_max,
        tri_centroids=centroids,
        tri_v0=v0, tri_v1=v1, tri_v2=v2,
    )


def body_aabb_overlaps(data_list: List[MeshCollisionData]) -> List[Tuple[int, int]]:
    """Find all body pairs whose AABBs overlap.

    Uses direct comparison -- O(n^2) but n is typically 3-10.

    Returns:
        List of (i, j) index pairs into data_list.
    """
    n = len(data_list)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = data_list[i], data_list[j]
            if np.all(a.body_aabb_min <= b.body_aabb_max) and \
               np.all(a.body_aabb_max >= b.body_aabb_min):
                pairs.append((i, j))
    return pairs


def find_triangle_collisions(
    data_a: MeshCollisionData,
    data_b: MeshCollisionData,
) -> List[Tuple[int, int, int, int]]:
    """Find colliding triangle pairs between two bodies.

    Uses NumPy broadcasting to test ALL MxN triangle AABB pairs
    in a single vectorized operation.

    Args:
        data_a: Pre-computed collision data for body A.
        data_b: Pre-computed collision data for body B.

    Returns:
        List of (body_a_idx, face_a_idx, body_b_idx, face_b_idx) tuples.
    """
    a_min = data_a.tri_aabb_min[:, None, :]
    a_max = data_a.tri_aabb_max[:, None, :]
    b_min = data_b.tri_aabb_min[None, :, :]
    b_max = data_b.tri_aabb_max[None, :, :]

    overlap = (a_min <= b_max) & (a_max >= b_min)
    colliding = overlap[:, :, 0] & overlap[:, :, 1] & overlap[:, :, 2]

    fi_a, fi_b = np.where(colliding)
    bi_a = data_a.body_index
    bi_b = data_b.body_index

    return [(bi_a, int(fa), bi_b, int(fb)) for fa, fb in zip(fi_a, fi_b)]


def _closest_point_on_triangle(p, a, b, c):
    """Closest point on triangle ABC to point P (Ericson 2004, 5.1.5)."""
    ab = b - a; ac = c - a; ap = p - a
    d1 = ab.dot(ap); d2 = ac.dot(ap)
    if d1 <= 0 and d2 <= 0:
        return a.copy()

    bp = p - b
    d3 = ab.dot(bp); d4 = ac.dot(bp)
    if d3 >= 0 and d4 <= d3:
        return b.copy()

    cp = p - c
    d5 = ab.dot(cp); d6 = ac.dot(cp)
    if d6 >= 0 and d5 <= d6:
        return c.copy()

    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        return a + v * ab

    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        return a + w * ac

    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + w * (c - b)

    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return a + ab * v + ac * w


def find_nearest_surface_vectorized(
    probe: np.ndarray,
    data_list: List[MeshCollisionData],
    top_k: int = 5,
) -> Tuple[np.ndarray, float]:
    """Find the nearest surface point to the probe using vectorized centroid search.

    Args:
        probe: Query point (3,).
        data_list: Pre-computed collision data for all bodies.
        top_k: Number of candidate triangles for detailed test.

    Returns:
        (nearest_point, distance) or (probe, inf) if no bodies.
    """
    if not data_list:
        return probe.copy(), float('inf')

    all_centroids = np.concatenate([d.tri_centroids for d in data_list])
    all_v0 = np.concatenate([d.tri_v0 for d in data_list])
    all_v1 = np.concatenate([d.tri_v1 for d in data_list])
    all_v2 = np.concatenate([d.tri_v2 for d in data_list])

    diffs = all_centroids - probe[None, :]
    sq_dists = np.sum(diffs * diffs, axis=1)

    k = min(top_k, len(sq_dists))
    nearest_idx = np.argpartition(sq_dists, k)[:k]

    best_dist = float('inf')
    best_point = probe.copy()

    for idx in nearest_idx:
        pt = _closest_point_on_triangle(probe, all_v0[idx], all_v1[idx], all_v2[idx])
        d = np.linalg.norm(probe - pt)
        if d < best_dist:
            best_dist = d
            best_point = pt

    return best_point, best_dist


def detect_all_collisions(bodies: list) -> Tuple[List[MeshCollisionData], List[Tuple[int, int, int, int]]]:
    """Run the full hierarchical collision detection pipeline.

    Args:
        bodies: List of body instances.

    Returns:
        (collision_data_list, collision_pairs)
    """
    data_list = [precompute_collision_data(b, i) for i, b in enumerate(bodies)]
    body_pairs = body_aabb_overlaps(data_list)

    all_collisions = []
    for i, j in body_pairs:
        pairs = find_triangle_collisions(data_list[i], data_list[j])
        all_collisions.extend(pairs)

    return data_list, all_collisions


class AABBTree(SpatialStructure):
    """AABB-based spatial structure wrapping the vectorized collision pipeline."""

    def __init__(self, **kwargs):
        self._data_list: List[MeshCollisionData] = []
        self._collision_pairs: List[Tuple[int, int, int, int]] = []

    def build(self, bodies) -> None:
        """Build AABB data for all bodies."""
        self._data_list, self._collision_pairs = detect_all_collisions(bodies)

    def query_collisions(self) -> List[Tuple[int, int, int, int]]:
        """Return collision pairs from the last build."""
        return self._collision_pairs

    def query_nearest(self, probe: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, float]:
        """Find nearest surface point using vectorized centroid search."""
        return find_nearest_surface_vectorized(probe, self._data_list, top_k)

    def get_viz_data(self, max_depth: int = 6) -> List[dict]:
        """Return AABB visualization data for all bodies."""
        viz = []
        for d in self._data_list:
            center = ((d.body_aabb_min + d.body_aabb_max) / 2).tolist()
            size = (d.body_aabb_max - d.body_aabb_min).tolist()
            viz.append({
                'type': 'aabb',
                'center': center,
                'size': size,
                'depth': 0,
                'body_index': d.body_index,
            })
        return viz
