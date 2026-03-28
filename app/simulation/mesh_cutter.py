"""
Mesh cutting operations for deformable body simulation.

Implements topology-changing operations where a deformable mesh is
split along a cutting plane. This is essential for surgical simulation
(the original project's primary use case).

The cutting algorithm:
1. Define a cutting plane from the probe trajectory (2 points + normal)
2. Classify all vertices as above/below the plane
3. Find edges that cross the plane
4. Create new vertices at intersection points
5. Split faces that straddle the plane into smaller triangles
6. Rebuild the spring network for the modified topology

References:
    - Bielser & Gross (2000), Interactive simulation of surgical cuts
    - Nienhuys & van der Stappen (2001), A surgery simulation
      supporting cuts and finite element deformation
"""
import numpy as np
from typing import Tuple, Optional


def cut_mesh_with_plane(
    vertices: np.ndarray,
    faces: np.ndarray,
    plane_point: np.ndarray,
    plane_normal: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Split a triangle mesh along a plane.

    Classifies each vertex as above (+) or below (-) the cutting plane,
    then splits triangles that straddle the plane by inserting new
    vertices at the edge-plane intersections.

    Args:
        vertices: (N, 3) vertex positions.
        faces: (F, 3) triangle indices.
        plane_point: A point on the cutting plane (3,).
        plane_normal: Unit normal of the cutting plane (3,).

    Returns:
        (new_vertices, new_faces) with the mesh split along the plane.
    """
    plane_point = np.asarray(plane_point, dtype=np.float64)
    plane_normal = np.asarray(plane_normal, dtype=np.float64)
    plane_normal = plane_normal / (np.linalg.norm(plane_normal) + 1e-10)

    # Signed distance of each vertex from the plane
    # d > 0: above, d < 0: below, d ~ 0: on plane
    dists = (vertices - plane_point) @ plane_normal  # (N,)

    # Classify vertices
    signs = np.sign(dists)  # +1, -1, or 0
    signs[np.abs(dists) < 1e-8] = 0  # on plane

    new_verts = list(vertices)
    new_faces = []

    # Cache for edge intersection vertices to avoid duplicates
    # Key: (min_idx, max_idx), Value: new vertex index
    edge_cache = {}

    for face in faces:
        i0, i1, i2 = face
        s0, s1, s2 = signs[i0], signs[i1], signs[i2]

        # Case 1: All on same side (or on plane) -- keep face
        if s0 >= 0 and s1 >= 0 and s2 >= 0:
            new_faces.append([i0, i1, i2])
            continue
        if s0 <= 0 and s1 <= 0 and s2 <= 0:
            new_faces.append([i0, i1, i2])
            continue

        # Case 2: Triangle straddles the plane -- split
        # Find the vertex on one side and the two on the other
        verts_above = [i for i, s in zip(face, [s0, s1, s2]) if s > 0]
        verts_below = [i for i, s in zip(face, [s0, s1, s2]) if s < 0]
        verts_on = [i for i, s in zip(face, [s0, s1, s2]) if s == 0]

        if len(verts_on) == 1 and len(verts_above) == 1 and len(verts_below) == 1:
            # One vertex on plane: split into 2 triangles at the crossing edge
            a = verts_above[0]
            b = verts_below[0]
            c = verts_on[0]
            # Find intersection of edge a-b with plane
            new_idx = _get_or_create_intersection(
                a, b, vertices, dists, new_verts, edge_cache
            )
            new_faces.append([a, new_idx, c])
            new_faces.append([new_idx, b, c])

        elif len(verts_above) == 1 and len(verts_below) == 2:
            a = verts_above[0]
            b, c = verts_below
            ab = _get_or_create_intersection(a, b, vertices, dists, new_verts, edge_cache)
            ac = _get_or_create_intersection(a, c, vertices, dists, new_verts, edge_cache)
            new_faces.append([a, ab, ac])
            new_faces.append([ab, b, c])
            new_faces.append([ab, c, ac])

        elif len(verts_below) == 1 and len(verts_above) == 2:
            a = verts_below[0]
            b, c = verts_above
            ab = _get_or_create_intersection(a, b, vertices, dists, new_verts, edge_cache)
            ac = _get_or_create_intersection(a, c, vertices, dists, new_verts, edge_cache)
            new_faces.append([a, ab, ac])
            new_faces.append([ab, b, c])
            new_faces.append([ab, c, ac])

        else:
            # Edge case (2 on plane, etc.) -- keep original
            new_faces.append([i0, i1, i2])

    return np.array(new_verts), np.array(new_faces, dtype=np.int32)


def _get_or_create_intersection(
    idx_a, idx_b, vertices, dists, new_verts, edge_cache
):
    """Get or create the intersection vertex on edge a-b."""
    key = (min(idx_a, idx_b), max(idx_a, idx_b))
    if key in edge_cache:
        return edge_cache[key]

    # Interpolation parameter
    da, db = abs(dists[idx_a]), abs(dists[idx_b])
    t = da / (da + db + 1e-10)

    # New vertex position
    new_pos = vertices[idx_a] * (1 - t) + vertices[idx_b] * t
    new_idx = len(new_verts)
    new_verts.append(new_pos)
    edge_cache[key] = new_idx
    return new_idx


def cut_deformable_body(body, plane_point, plane_normal):
    """Apply a planar cut to a DeformableBody, modifying it in-place.

    After cutting:
    1. Vertices and faces are updated with the split mesh
    2. The spring network is rebuilt from the new topology
    3. Normals and AABB are recomputed

    Args:
        body: DeformableBody to cut.
        plane_point: Point on the cutting plane (3,).
        plane_normal: Normal of the cutting plane (3,).

    Returns:
        Number of new vertices created by the cut.
    """
    old_n = len(body.vertices)

    new_verts, new_faces = cut_mesh_with_plane(
        body.vertices, body.faces, plane_point, plane_normal
    )

    new_n = len(new_verts)
    n_created = new_n - old_n

    if n_created == 0:
        return 0  # No cut happened

    # Update body
    body.vertices = np.array(new_verts, dtype=np.float64)
    body.faces = np.array(new_faces, dtype=np.int32)

    # Extend velocity and mass arrays for new vertices
    if hasattr(body, 'velocities') and body.velocities is not None:
        new_velocities = np.zeros((n_created, 3), dtype=np.float64)
        body.velocities = np.concatenate([body.velocities, new_velocities])

    if hasattr(body, 'masses') and body.masses is not None:
        # New vertices get average mass of neighbors
        avg_mass = np.mean(body.masses)
        new_masses = np.full(n_created, avg_mass)
        body.masses = np.concatenate([body.masses, new_masses])

    if hasattr(body, 'rest_vertices'):
        # Rest positions for new vertices = current positions
        body.rest_vertices = body.vertices.copy()

    # Rebuild spring network from new topology
    if hasattr(body, 'build_spring_network'):
        body.build_spring_network()

    # Recompute normals and AABB
    body._compute_normals()
    body._compute_aabb()

    return n_created
