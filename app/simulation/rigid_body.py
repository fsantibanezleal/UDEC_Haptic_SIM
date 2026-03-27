"""
Rigid Body representation for 3D haptic simulation.

===== PHYSICAL MODEL =====

A rigid body is a 3D object that does not deform under applied forces.
Its state is fully described by:
    - Position: center of mass p = (x, y, z)
    - Orientation: rotation matrix R in SO(3) or quaternion q
    - Linear velocity: v = dp/dt
    - Angular velocity: omega (rotation rate vector)

For the haptic simulation, we use a simplified model where:
    - Objects can be translated and rotated by user input
    - Collision detection uses the mesh surface triangles
    - Force feedback is computed as spring forces at contact points

===== MESH REPRESENTATION =====

The mesh is stored as:
    - vertices: Nx3 array of 3D positions
    - faces: Mx3 array of triangle vertex indices
    - normals: Mx3 array of face normals (computed from cross products)

Face normal computation:
    n_hat = normalize((v1 - v0) x (v2 - v0))

This matches the original C++ NormalP() function from Cuerpo.cpp.

===== BOUNDING VOLUME =====

An axis-aligned bounding box (AABB) is maintained for fast broad-phase
rejection in collision detection.  The AABB is recomputed after every
geometric transformation (translate, rotate, scale).

===== REFERENCES =====

- Baraff & Witkin (1997), Physically Based Modeling, SIGGRAPH Course Notes
- Original C++ Cuerpo struct from UDEC Haptic SIM (2008)
- Ericson (2004), Real-Time Collision Detection, Morgan Kaufmann
"""
import numpy as np
from typing import Optional, List


class RigidBody:
    """A rigid body with triangle mesh geometry.

    The rigid body is the fundamental simulation entity.  It owns a
    triangle mesh described by *vertices* and *faces*, maintains
    per-face unit normals, and tracks an axis-aligned bounding box
    (AABB) that is kept in sync with any geometric transformation.

    Attributes
    ----------
    name : str
        Human-readable identifier.
    vertices : np.ndarray
        (N, 3) array of vertex positions in world space.
    faces : np.ndarray
        (M, 3) array of triangle face indices into *vertices*.
    normals : np.ndarray
        (M, 3) array of per-face unit normals.
    color : list[float]
        RGBA color as [r, g, b, a] in [0, 1].
    position : np.ndarray
        Centroid (mean of vertices) [x, y, z].
    velocity : np.ndarray
        Linear velocity [vx, vy, vz].
    collision_faces : set[int]
        Face indices currently flagged as colliding.
    aabb_min : np.ndarray
        Axis-aligned bounding box minimum corner.
    aabb_max : np.ndarray
        Axis-aligned bounding box maximum corner.
    """

    def __init__(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        name: str = "body",
        color: Optional[List[float]] = None,
    ):
        """Initialise rigid body from mesh data.

        Parameters
        ----------
        vertices : array_like, shape (N, 3)
            3D vertex positions.
        faces : array_like, shape (M, 3)
            Triangle vertex indices (0-based).
        name : str, optional
            Display name, default ``"body"``.
        color : list[float], optional
            RGBA colour.  Default light grey ``[0.7, 0.7, 0.8, 1.0]``.
        """
        self.name = name
        self.vertices = np.array(vertices, dtype=np.float64)
        self.faces = np.array(faces, dtype=np.int32)
        self.color = color or [0.7, 0.7, 0.8, 1.0]

        self.position = np.mean(self.vertices, axis=0).copy()
        self.velocity = np.zeros(3, dtype=np.float64)

        self.collision_faces: set = set()

        self._compute_normals()
        self._compute_aabb()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_normals(self) -> None:
        """Compute per-face normals via cross product.

        For triangle (v0, v1, v2)::

            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = normalize(edge1 x edge2)

        Degenerate triangles receive a fallback normal of [0, 0, 1].
        """
        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]

        edge1 = v1 - v0
        edge2 = v2 - v0
        cross = np.cross(edge1, edge2)

        norms = np.linalg.norm(cross, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        self.normals = cross / norms

    def _compute_aabb(self) -> None:
        """Compute axis-aligned bounding box from current vertices."""
        self.aabb_min = np.min(self.vertices, axis=0)
        self.aabb_max = np.max(self.vertices, axis=0)

    # ------------------------------------------------------------------
    # Geometric transformations
    # ------------------------------------------------------------------

    def translate(self, delta: np.ndarray) -> None:
        """Translate all vertices by *delta* ``[dx, dy, dz]``.

        The AABB and centroid are updated incrementally (O(1)).
        """
        delta = np.asarray(delta, dtype=np.float64)
        self.vertices += delta
        self.position += delta
        self.aabb_min += delta
        self.aabb_max += delta

    def scale(self, factor: float, pivot: Optional[np.ndarray] = None) -> None:
        """Scale about a pivot point (default: centroid).

        ``p_new = pivot + factor * (p_old - pivot)``
        """
        if pivot is None:
            pivot = self.position.copy()
        pivot = np.asarray(pivot, dtype=np.float64)
        self.vertices = pivot + factor * (self.vertices - pivot)
        self.position = pivot + factor * (self.position - pivot)
        self._compute_aabb()

    def rotate(
        self,
        axis: np.ndarray,
        angle_deg: float,
        pivot: Optional[np.ndarray] = None,
    ) -> None:
        """Rotate about an axis through a pivot point.

        Uses **Rodrigues' rotation formula**::

            v_rot = v*cos(t) + (k x v)*sin(t) + k*(k . v)*(1 - cos(t))

        where *k* is the unit rotation axis and *t* is the angle in
        radians.
        """
        if pivot is None:
            pivot = self.position.copy()
        pivot = np.asarray(pivot, dtype=np.float64)
        axis = np.asarray(axis, dtype=np.float64)
        axis = axis / (np.linalg.norm(axis) + 1e-10)

        theta = np.radians(angle_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        centered = self.vertices - pivot

        # Rodrigues' formula (vectorised)
        dot = np.sum(centered * axis, axis=1, keepdims=True)
        cross = np.cross(centered, axis)

        rotated = centered * cos_t - cross * sin_t + axis * dot * (1 - cos_t)

        self.vertices = rotated + pivot
        self.position = np.mean(self.vertices, axis=0)
        self._compute_normals()
        self._compute_aabb()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_face_vertices(self, face_idx: int) -> np.ndarray:
        """Return the 3 vertex positions for face *face_idx*.

        Returns
        -------
        np.ndarray, shape (3, 3)
            Each row is a vertex ``[x, y, z]``.
        """
        return self.vertices[self.faces[face_idx]]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def get_state(self) -> dict:
        """Serialise for WebSocket / Three.js consumption."""
        return {
            "name": self.name,
            "vertices": self.vertices.tolist(),
            "faces": self.faces.tolist(),
            "normals": self.normals.tolist(),
            "color": self.color,
            "position": self.position.tolist(),
            "collision_faces": list(self.collision_faces),
            "aabb_min": self.aabb_min.tolist(),
            "aabb_max": self.aabb_max.tolist(),
        }
