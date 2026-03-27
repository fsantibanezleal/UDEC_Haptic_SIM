"""
Octree spatial structure for collision detection.

Recursive 8-child octree with vectorized centroid assignment.
Uses BFS queue for construction (iterative, not recursive).
Nodes stored as flat list for efficient traversal.

References:
    - Original C++ Octrees.cpp from UDEC Haptic SIM (2008)
    - Ericson (2004), Real-Time Collision Detection, Ch. 7
"""
import numpy as np
from typing import List, Tuple
from collections import deque
from dataclasses import dataclass, field

from .base import SpatialStructure
from .aabb_tree import _closest_point_on_triangle


@dataclass
class OctreeNode:
    """A single node in the octree."""
    node_min: np.ndarray
    node_max: np.ndarray
    depth: int
    tri_indices: np.ndarray  # indices into the global triangle arrays
    body_indices: np.ndarray  # body index for each triangle
    children: list = field(default_factory=list)
    is_leaf: bool = True


class Octree(SpatialStructure):
    """Recursive 8-child octree with vectorized centroid assignment.

    Construction uses BFS queue for iterative building.
    Leaf nodes contain triangles; internal nodes split space into 8 octants.
    """

    def __init__(self, max_depth: int = 8, min_triangles: int = 4, **kwargs):
        self.max_depth = max_depth
        self.min_triangles = min_triangles
        self.nodes: List[OctreeNode] = []
        self.root: OctreeNode = None

        # Global triangle data (concatenated across all bodies)
        self._centroids = None
        self._v0 = None
        self._v1 = None
        self._v2 = None
        self._body_ids = None
        self._tri_face_ids = None
        self._tri_aabb_min = None
        self._tri_aabb_max = None

    def build(self, bodies) -> None:
        """Build the octree from a list of bodies using BFS construction."""
        self.nodes = []
        self.root = None

        if not bodies:
            return

        # Collect all triangles across all bodies
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

        # Compute root bounding box
        global_min = self._tri_aabb_min.min(axis=0) - 0.01
        global_max = self._tri_aabb_max.max(axis=0) + 0.01

        self.root = OctreeNode(
            node_min=global_min,
            node_max=global_max,
            depth=0,
            tri_indices=all_indices,
            body_indices=self._body_ids.copy(),
        )
        self.nodes = [self.root]

        # BFS construction
        queue = deque([self.root])
        while queue:
            node = queue.popleft()

            if node.depth >= self.max_depth or len(node.tri_indices) <= self.min_triangles:
                node.is_leaf = True
                continue

            node.is_leaf = False
            mid = (node.node_min + node.node_max) / 2

            # Vectorized octant assignment
            tri_cents = self._centroids[node.tri_indices]
            gt = tri_cents > mid  # (N, 3) boolean
            octant = gt[:, 0].astype(np.int32) * 4 + gt[:, 1].astype(np.int32) * 2 + gt[:, 2].astype(np.int32)

            for oct_idx in range(8):
                mask = octant == oct_idx
                if not np.any(mask):
                    continue

                child_tri_indices = node.tri_indices[mask]
                child_body_indices = node.body_indices[mask]

                # Compute child bounding box
                ox = (oct_idx >> 2) & 1
                oy = (oct_idx >> 1) & 1
                oz = oct_idx & 1

                child_min = np.array([
                    mid[0] if ox else node.node_min[0],
                    mid[1] if oy else node.node_min[1],
                    mid[2] if oz else node.node_min[2],
                ])
                child_max = np.array([
                    node.node_max[0] if ox else mid[0],
                    node.node_max[1] if oy else mid[1],
                    node.node_max[2] if oz else mid[2],
                ])

                child = OctreeNode(
                    node_min=child_min,
                    node_max=child_max,
                    depth=node.depth + 1,
                    tri_indices=child_tri_indices,
                    body_indices=child_body_indices,
                )
                node.children.append(child)
                self.nodes.append(child)
                queue.append(child)

    def query_collisions(self) -> List[Tuple[int, int, int, int]]:
        """Find collisions by checking leaf nodes with triangles from multiple bodies."""
        collisions = []
        if self.root is None:
            return collisions

        seen = set()

        for node in self.nodes:
            if not node.is_leaf or len(node.tri_indices) < 2:
                continue

            # Check if this leaf has triangles from multiple bodies
            unique_bodies = np.unique(node.body_indices)
            if len(unique_bodies) < 2:
                continue

            # Test all cross-body pairs using AABB overlap
            for i in range(len(unique_bodies)):
                for j in range(i + 1, len(unique_bodies)):
                    bi, bj = unique_bodies[i], unique_bodies[j]
                    mask_i = node.body_indices == bi
                    mask_j = node.body_indices == bj

                    idx_i = node.tri_indices[mask_i]
                    idx_j = node.tri_indices[mask_j]

                    # Vectorized AABB overlap test
                    a_min = self._tri_aabb_min[idx_i][:, None, :]
                    a_max = self._tri_aabb_max[idx_i][:, None, :]
                    b_min = self._tri_aabb_min[idx_j][None, :, :]
                    b_max = self._tri_aabb_max[idx_j][None, :, :]

                    overlap = (a_min <= b_max) & (a_max >= b_min)
                    colliding = overlap[:, :, 0] & overlap[:, :, 1] & overlap[:, :, 2]

                    fi_a, fi_b = np.where(colliding)
                    for fa, fb in zip(fi_a, fi_b):
                        face_a = int(self._tri_face_ids[idx_i[fa]])
                        face_b = int(self._tri_face_ids[idx_j[fb]])
                        key = (int(bi), face_a, int(bj), face_b)
                        if key not in seen:
                            seen.add(key)
                            collisions.append(key)

        return collisions

    def query_nearest(self, probe: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, float]:
        """Find nearest surface point using centroid pre-filter."""
        if self._centroids is None or len(self._centroids) == 0:
            return probe.copy(), float('inf')

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
        """Return octree node visualization data up to max_depth."""
        viz = []
        for node in self.nodes:
            if node.depth > max_depth:
                continue
            center = ((node.node_min + node.node_max) / 2).tolist()
            size = (node.node_max - node.node_min).tolist()
            viz.append({
                'type': 'octree',
                'center': center,
                'size': size,
                'depth': node.depth,
                'tri_count': len(node.tri_indices),
                'is_leaf': node.is_leaf,
            })
        return viz

    def get_depth(self) -> int:
        """Return the maximum depth of the octree."""
        if not self.nodes:
            return 0
        return max(n.depth for n in self.nodes)

    def get_triangle_count(self) -> int:
        """Return total number of triangles."""
        if self._centroids is None:
            return 0
        return len(self._centroids)
