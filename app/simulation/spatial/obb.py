"""
Oriented Bounding Box (OBB) Tree spatial structure.

Uses PCA to compute oriented bounding boxes for each body,
then performs SAT (Separating Axis Theorem) overlap tests
using 15 axes (3+3+9 cross products).

References:
    - Gottschalk et al. (1996), OBBTree: A Hierarchical Structure for
      Rapid Interference Detection
    - Ericson (2004), Real-Time Collision Detection, Ch. 4.4
"""
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from .base import SpatialStructure
from .aabb_tree import _closest_point_on_triangle


@dataclass
class OBBData:
    """Oriented Bounding Box data for a body."""
    body_index: int
    center: np.ndarray       # (3,) center of OBB
    axes: np.ndarray         # (3, 3) columns are local axes
    half_extents: np.ndarray  # (3,) half-extents along each axis
    tri_centroids: np.ndarray
    tri_v0: np.ndarray
    tri_v1: np.ndarray
    tri_v2: np.ndarray
    tri_aabb_min: np.ndarray
    tri_aabb_max: np.ndarray
    tri_face_ids: np.ndarray


def compute_obb(body, body_index: int) -> OBBData:
    """Compute PCA-based OBB for a body.

    Args:
        body: Body with vertices (N,3) and faces (F,3).
        body_index: Index of this body in the scene.

    Returns:
        OBBData with center, axes, half_extents.
    """
    V = body.vertices
    faces = body.faces
    center = V.mean(axis=0)
    centered = V - center

    # PCA via covariance matrix
    cov = centered.T @ centered / len(V)
    eigvals, axes = np.linalg.eigh(cov)

    # Project vertices onto PCA axes
    proj = centered @ axes
    half_extents = (proj.max(axis=0) - proj.min(axis=0)) / 2

    # Triangle data
    v0 = V[faces[:, 0]]
    v1 = V[faces[:, 1]]
    v2 = V[faces[:, 2]]
    stacked = np.stack([v0, v1, v2], axis=1)
    tri_min = stacked.min(axis=1)
    tri_max = stacked.max(axis=1)
    centroids = stacked.mean(axis=1)

    return OBBData(
        body_index=body_index,
        center=center,
        axes=axes,
        half_extents=half_extents,
        tri_centroids=centroids,
        tri_v0=v0, tri_v1=v1, tri_v2=v2,
        tri_aabb_min=tri_min,
        tri_aabb_max=tri_max,
        tri_face_ids=np.arange(len(faces), dtype=np.int32),
    )


def obb_overlap(a: OBBData, b: OBBData) -> bool:
    """Test OBB overlap using SAT with 15 axes (3+3+9).

    Args:
        a: First OBB.
        b: Second OBB.

    Returns:
        True if OBBs overlap.
    """
    d = b.center - a.center
    axes_a = a.axes.T  # (3, 3) rows are axes
    axes_b = b.axes.T

    # Test 15 separating axes
    test_axes = []
    # 3 axes from A
    for i in range(3):
        test_axes.append(axes_a[i])
    # 3 axes from B
    for i in range(3):
        test_axes.append(axes_b[i])
    # 9 cross products
    for i in range(3):
        for j in range(3):
            cross = np.cross(axes_a[i], axes_b[j])
            norm = np.linalg.norm(cross)
            if norm > 1e-10:
                test_axes.append(cross / norm)

    for axis in test_axes:
        # Project half-extents onto axis
        proj_a = sum(a.half_extents[i] * abs(np.dot(axes_a[i], axis)) for i in range(3))
        proj_b = sum(b.half_extents[i] * abs(np.dot(axes_b[i], axis)) for i in range(3))
        dist = abs(np.dot(d, axis))

        if dist > proj_a + proj_b:
            return False  # Separating axis found

    return True  # No separating axis found, OBBs overlap


class OBBTree(SpatialStructure):
    """PCA-based Oriented Bounding Box spatial structure."""

    def __init__(self, **kwargs):
        self._obb_data: List[OBBData] = []
        self._all_centroids = None
        self._all_v0 = None
        self._all_v1 = None
        self._all_v2 = None

    def build(self, bodies) -> None:
        """Build OBBs for all bodies."""
        self._obb_data = []
        if not bodies:
            self._all_centroids = None
            return

        for i, body in enumerate(bodies):
            self._obb_data.append(compute_obb(body, i))

        # Concatenate for nearest query
        self._all_centroids = np.concatenate([d.tri_centroids for d in self._obb_data])
        self._all_v0 = np.concatenate([d.tri_v0 for d in self._obb_data])
        self._all_v1 = np.concatenate([d.tri_v1 for d in self._obb_data])
        self._all_v2 = np.concatenate([d.tri_v2 for d in self._obb_data])

    def query_collisions(self) -> List[Tuple[int, int, int, int]]:
        """Find collisions using OBB broad phase + triangle AABB narrow phase."""
        collisions = []
        n = len(self._obb_data)

        for i in range(n):
            for j in range(i + 1, n):
                a, b = self._obb_data[i], self._obb_data[j]
                if not obb_overlap(a, b):
                    continue

                # Triangle-level AABB test
                a_min = a.tri_aabb_min[:, None, :]
                a_max = a.tri_aabb_max[:, None, :]
                b_min = b.tri_aabb_min[None, :, :]
                b_max = b.tri_aabb_max[None, :, :]

                overlap = (a_min <= b_max) & (a_max >= b_min)
                coll = overlap[:, :, 0] & overlap[:, :, 1] & overlap[:, :, 2]

                fi_a, fi_b = np.where(coll)
                for fa, fb in zip(fi_a, fi_b):
                    collisions.append((a.body_index, int(fa), b.body_index, int(fb)))

        return collisions

    def query_nearest(self, probe: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, float]:
        """Find nearest surface point."""
        if self._all_centroids is None or len(self._all_centroids) == 0:
            return probe.copy(), float('inf')

        diffs = self._all_centroids - probe[None, :]
        sq_dists = np.sum(diffs * diffs, axis=1)

        k = min(top_k, len(sq_dists))
        nearest_idx = np.argpartition(sq_dists, k)[:k]

        best_dist = float('inf')
        best_point = probe.copy()

        for idx in nearest_idx:
            pt = _closest_point_on_triangle(probe, self._all_v0[idx], self._all_v1[idx], self._all_v2[idx])
            d = np.linalg.norm(probe - pt)
            if d < best_dist:
                best_dist = d
                best_point = pt

        return best_point, best_dist

    def get_viz_data(self, max_depth: int = 6) -> List[dict]:
        """Return OBB visualization data for all bodies."""
        viz = []
        for d in self._obb_data:
            viz.append({
                'type': 'obb',
                'center': d.center.tolist(),
                'axes': d.axes.tolist(),
                'half_extents': d.half_extents.tolist(),
                'depth': 0,
                'body_index': d.body_index,
            })
        return viz
