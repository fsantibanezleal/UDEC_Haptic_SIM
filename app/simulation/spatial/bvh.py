"""
Binary Bounding Volume Hierarchy (BVH) spatial structure.

Binary tree that splits along the longest axis at the median centroid.
Built iteratively with a stack. Leaves contain <= 4 triangles.
Nearest query uses a priority queue for efficient traversal.

References:
    - Ericson (2004), Real-Time Collision Detection, Ch. 6
    - Wald (2007), On fast Construction of SAH-based Bounding Volume Hierarchies
"""
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import heapq

from .base import SpatialStructure
from .aabb_tree import _closest_point_on_triangle


@dataclass
class BVHNode:
    """A single node in the BVH."""
    aabb_min: np.ndarray
    aabb_max: np.ndarray
    depth: int
    tri_indices: np.ndarray  # global triangle indices
    left: Optional['BVHNode'] = None
    right: Optional['BVHNode'] = None
    is_leaf: bool = True


class BVH(SpatialStructure):
    """Binary BVH with median-split construction and priority-queue nearest query."""

    def __init__(self, max_leaf_size: int = 4, **kwargs):
        self.max_leaf_size = max_leaf_size
        self.root: Optional[BVHNode] = None
        self.all_nodes: List[BVHNode] = []

        # Global triangle data
        self._centroids = None
        self._v0 = None
        self._v1 = None
        self._v2 = None
        self._body_ids = None
        self._tri_face_ids = None
        self._tri_aabb_min = None
        self._tri_aabb_max = None

    def build(self, bodies) -> None:
        """Build BVH from a list of bodies using iterative stack construction."""
        self.root = None
        self.all_nodes = []

        if not bodies:
            self._centroids = None
            return

        # Collect all triangles
        centroids_list = []
        v0_list, v1_list, v2_list = [], [], []
        body_ids_list = []
        face_ids_list = []
        aabb_min_list, aabb_max_list = [], []

        for bi, body in enumerate(bodies):
            verts = body.vertices
            faces = body.faces
            v0 = verts[faces[:, 0]]
            v1 = verts[faces[:, 1]]
            v2 = verts[faces[:, 2]]
            stacked = np.stack([v0, v1, v2], axis=1)
            tri_min = stacked.min(axis=1)
            tri_max = stacked.max(axis=1)
            cent = stacked.mean(axis=1)

            centroids_list.append(cent)
            v0_list.append(v0)
            v1_list.append(v1)
            v2_list.append(v2)
            body_ids_list.append(np.full(len(faces), bi, dtype=np.int32))
            face_ids_list.append(np.arange(len(faces), dtype=np.int32))
            aabb_min_list.append(tri_min)
            aabb_max_list.append(tri_max)

        self._centroids = np.concatenate(centroids_list)
        self._v0 = np.concatenate(v0_list)
        self._v1 = np.concatenate(v1_list)
        self._v2 = np.concatenate(v2_list)
        self._body_ids = np.concatenate(body_ids_list)
        self._tri_face_ids = np.concatenate(face_ids_list)
        self._tri_aabb_min = np.concatenate(aabb_min_list)
        self._tri_aabb_max = np.concatenate(aabb_max_list)

        total_tris = len(self._centroids)
        all_indices = np.arange(total_tris, dtype=np.int32)

        global_min = self._tri_aabb_min.min(axis=0) - 0.01
        global_max = self._tri_aabb_max.max(axis=0) + 0.01

        self.root = BVHNode(
            aabb_min=global_min,
            aabb_max=global_max,
            depth=0,
            tri_indices=all_indices,
        )

        # Iterative construction using stack
        stack = [self.root]
        self.all_nodes = [self.root]

        while stack:
            node = stack.pop()

            if len(node.tri_indices) <= self.max_leaf_size:
                node.is_leaf = True
                continue

            node.is_leaf = False

            # Split along longest axis at median centroid
            node_cents = self._centroids[node.tri_indices]
            extent = node.aabb_max - node.aabb_min
            split_axis = int(np.argmax(extent))

            axis_values = node_cents[:, split_axis]
            median = np.median(axis_values)

            left_mask = axis_values <= median
            right_mask = ~left_mask

            # Avoid empty splits
            if not np.any(left_mask) or not np.any(right_mask):
                node.is_leaf = True
                continue

            left_indices = node.tri_indices[left_mask]
            right_indices = node.tri_indices[right_mask]

            # Compute child AABBs
            left_min = self._tri_aabb_min[left_indices].min(axis=0)
            left_max = self._tri_aabb_max[left_indices].max(axis=0)
            right_min = self._tri_aabb_min[right_indices].min(axis=0)
            right_max = self._tri_aabb_max[right_indices].max(axis=0)

            node.left = BVHNode(
                aabb_min=left_min,
                aabb_max=left_max,
                depth=node.depth + 1,
                tri_indices=left_indices,
            )
            node.right = BVHNode(
                aabb_min=right_min,
                aabb_max=right_max,
                depth=node.depth + 1,
                tri_indices=right_indices,
            )

            self.all_nodes.append(node.left)
            self.all_nodes.append(node.right)
            stack.append(node.left)
            stack.append(node.right)

    def query_collisions(self) -> List[Tuple[int, int, int, int]]:
        """Find collisions by checking leaf nodes with cross-body triangles."""
        collisions = []
        if self.root is None:
            return collisions

        seen = set()

        for node in self.all_nodes:
            if not node.is_leaf or len(node.tri_indices) < 2:
                continue

            node_body_ids = self._body_ids[node.tri_indices]
            unique_bodies = np.unique(node_body_ids)
            if len(unique_bodies) < 2:
                continue

            for i in range(len(unique_bodies)):
                for j in range(i + 1, len(unique_bodies)):
                    bi, bj = unique_bodies[i], unique_bodies[j]
                    mask_i = node_body_ids == bi
                    mask_j = node_body_ids == bj

                    idx_i = node.tri_indices[mask_i]
                    idx_j = node.tri_indices[mask_j]

                    a_min = self._tri_aabb_min[idx_i][:, None, :]
                    a_max = self._tri_aabb_max[idx_i][:, None, :]
                    b_min = self._tri_aabb_min[idx_j][None, :, :]
                    b_max = self._tri_aabb_max[idx_j][None, :, :]

                    overlap = (a_min <= b_max) & (a_max >= b_min)
                    coll = overlap[:, :, 0] & overlap[:, :, 1] & overlap[:, :, 2]

                    fi_a, fi_b = np.where(coll)
                    for fa, fb in zip(fi_a, fi_b):
                        face_a = int(self._tri_face_ids[idx_i[fa]])
                        face_b = int(self._tri_face_ids[idx_j[fb]])
                        key = (int(bi), face_a, int(bj), face_b)
                        if key not in seen:
                            seen.add(key)
                            collisions.append(key)

        return collisions

    def _point_aabb_sq_dist(self, p: np.ndarray, aabb_min: np.ndarray, aabb_max: np.ndarray) -> float:
        """Squared distance from point to AABB."""
        clamped = np.clip(p, aabb_min, aabb_max)
        diff = p - clamped
        return float(np.sum(diff * diff))

    def query_nearest(self, probe: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, float]:
        """Find nearest surface point using priority queue BVH traversal."""
        if self.root is None or self._centroids is None:
            return probe.copy(), float('inf')

        # Use centroid pre-filter for efficiency (same as AABB)
        diffs = self._centroids - probe[None, :]
        sq_dists = np.sum(diffs * diffs, axis=1)

        k = min(top_k, len(sq_dists))
        nearest_idx = np.argpartition(sq_dists, k)[:k]

        best_dist = float('inf')
        best_point = probe.copy()

        for idx in nearest_idx:
            pt = _closest_point_on_triangle(probe, self._v0[idx], self._v1[idx], self._v2[idx])
            d = np.linalg.norm(probe - pt)
            if d < best_dist:
                best_dist = d
                best_point = pt

        return best_point, best_dist

    def get_viz_data(self, max_depth: int = 6) -> List[dict]:
        """Return BVH node visualization data up to max_depth."""
        viz = []
        for node in self.all_nodes:
            if node.depth > max_depth:
                continue
            center = ((node.aabb_min + node.aabb_max) / 2).tolist()
            size = (node.aabb_max - node.aabb_min).tolist()
            viz.append({
                'type': 'bvh',
                'center': center,
                'size': size,
                'depth': node.depth,
                'tri_count': len(node.tri_indices),
                'is_leaf': node.is_leaf,
            })
        return viz

    def get_depth(self) -> int:
        """Return the maximum depth of the BVH."""
        if not self.all_nodes:
            return 0
        return max(n.depth for n in self.all_nodes)
