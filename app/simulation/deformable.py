"""
Deformable body with mass-spring or XPBD physics.

Provides soft body simulation using either:
    - MSD: Mass-Spring-Damper (explicit Euler integration)
    - XPBD: Extended Position-Based Dynamics with distance constraints

The spring network is built from the unique edges of the triangle mesh.
All computation is vectorized with NumPy -- no Python for-loops in hot paths.

References:
    - Muller et al. (2007), Position Based Dynamics
    - Macklin et al. (2016), XPBD: Position-Based Simulation of Compliant
      Constrained Dynamics
    - Provot (1995), Deformation Constraints in a Mass-Spring Model
"""
import numpy as np
from typing import Optional, List


class DeformableBody:
    """Soft body with mass-spring or XPBD physics."""

    body_type = "deformable"

    def __init__(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        name: str = "deformable",
        color: Optional[List[float]] = None,
        mass: float = 1.0,
        stiffness: float = 500.0,
        damping: float = 5.0,
        solver: str = "msd",
    ):
        """Initialize a deformable body.

        Args:
            vertices: (N, 3) vertex positions.
            faces: (F, 3) triangle face indices.
            name: Display name.
            color: RGBA color.
            mass: Per-vertex mass.
            stiffness: Spring stiffness.
            damping: Spring damping.
            solver: "msd" or "xpbd".
        """
        self.name = name
        self.vertices = np.array(vertices, dtype=np.float64)
        self.rest_vertices = self.vertices.copy()
        self.faces = np.array(faces, dtype=np.int32)
        self.color = color or [0.9, 0.4, 0.7, 1.0]

        self.position = np.mean(self.vertices, axis=0).copy()
        self.velocity = np.zeros(3, dtype=np.float64)
        self.collision_faces: set = set()

        n_verts = len(self.vertices)
        self.velocities = np.zeros((n_verts, 3), dtype=np.float64)
        self.masses = np.full(n_verts, mass, dtype=np.float64)

        self.stiffness = stiffness
        self.damping = damping
        self.solver = solver
        self.compliance = 1.0 / max(stiffness, 1e-10)  # for XPBD
        self.xpbd_iterations = 5

        # Build spring network and normals/AABB
        self.springs = np.zeros((0, 2), dtype=np.int32)
        self.spring_rest_lengths = np.zeros(0, dtype=np.float64)
        self.build_spring_network()
        self._compute_normals()
        self._compute_aabb()

    @staticmethod
    def from_rigid_body(body, mass: float = 1.0, stiffness: float = 500.0,
                        damping: float = 5.0, solver: str = "msd") -> 'DeformableBody':
        """Convert a RigidBody to a DeformableBody.

        Args:
            body: RigidBody instance.
            mass: Per-vertex mass.
            stiffness: Spring stiffness.
            damping: Spring damping.
            solver: "msd" or "xpbd".

        Returns:
            DeformableBody with the same mesh.
        """
        return DeformableBody(
            vertices=body.vertices.copy(),
            faces=body.faces.copy(),
            name=body.name,
            color=body.color[:],
            mass=mass,
            stiffness=stiffness,
            damping=damping,
            solver=solver,
        )

    def build_spring_network(self):
        """Extract unique edges from faces as structural springs.

        Each edge of each triangle becomes a spring. Duplicate edges
        are removed by sorting and unique-ifying.
        """
        if len(self.faces) == 0:
            return

        edges = np.vstack([
            self.faces[:, [0, 1]],
            self.faces[:, [1, 2]],
            self.faces[:, [0, 2]],
        ])
        edges = np.sort(edges, axis=1)
        self.springs = np.unique(edges, axis=0)

        verts = self.vertices
        self.spring_rest_lengths = np.linalg.norm(
            verts[self.springs[:, 1]] - verts[self.springs[:, 0]], axis=1
        )

    def step_msd(self, dt: float = 1.0 / 60.0, gravity: float = -9.81,
                 floor_y: float = -1.5):
        """Vectorized Mass-Spring-Damper step.

        Uses semi-implicit Euler integration with spring forces,
        damping, gravity, and floor collision response.
        """
        if len(self.springs) == 0:
            return

        verts = self.vertices
        vels = self.velocities

        # Spring forces
        d = verts[self.springs[:, 1]] - verts[self.springs[:, 0]]
        lengths = np.linalg.norm(d, axis=1, keepdims=True)
        dirs = d / np.maximum(lengths, 1e-10)
        stretch = lengths.squeeze() - self.spring_rest_lengths

        f_spring = self.stiffness * stretch[:, None] * dirs

        # Damping forces along spring direction
        dv = vels[self.springs[:, 1]] - vels[self.springs[:, 0]]
        f_damp = self.damping * np.sum(dv * dirs, axis=1, keepdims=True) * dirs

        # Accumulate forces per vertex
        forces = np.zeros_like(verts)
        np.add.at(forces, self.springs[:, 0], f_spring + f_damp)
        np.add.at(forces, self.springs[:, 1], -(f_spring + f_damp))

        # Gravity
        forces[:, 1] += self.masses * gravity

        # Semi-implicit Euler
        vels += (forces / self.masses[:, None]) * dt
        vels *= 0.999  # global damping
        verts += vels * dt

        # Floor collision
        below = verts[:, 1] < floor_y
        verts[below, 1] = floor_y
        vels[below, 1] *= -0.3  # bounce

        # Update derived quantities
        self.vertices = verts
        self.velocities = vels
        self.position = np.mean(self.vertices, axis=0)
        self._compute_normals()
        self._compute_aabb()

    def step_xpbd(self, dt: float = 1.0 / 60.0, iterations: int = None,
                  gravity: float = -9.81, floor_y: float = -1.5):
        """XPBD with distance constraints.

        Extended Position-Based Dynamics solver with compliance parameter
        for more stable and controllable soft body simulation.
        """
        if len(self.springs) == 0:
            return

        if iterations is None:
            iterations = self.xpbd_iterations

        verts = self.vertices
        vels = self.velocities

        # Predict positions
        vels += np.array([0, gravity, 0]) * dt
        predicted = verts + vels * dt

        compliance = self.compliance

        # Solve constraints iteratively
        for _ in range(iterations):
            d = predicted[self.springs[:, 1]] - predicted[self.springs[:, 0]]
            lengths = np.linalg.norm(d, axis=1, keepdims=True)
            dirs = d / np.maximum(lengths, 1e-10)
            correction = lengths.squeeze() - self.spring_rest_lengths

            inv_mass_0 = 1.0 / self.masses[self.springs[:, 0]]
            inv_mass_1 = 1.0 / self.masses[self.springs[:, 1]]
            inv_mass_sum = inv_mass_0 + inv_mass_1

            delta = correction / (inv_mass_sum + compliance / (dt * dt))

            delta_0 = (delta * inv_mass_0 / inv_mass_sum)[:, None] * dirs
            delta_1 = (delta * inv_mass_1 / inv_mass_sum)[:, None] * dirs

            np.add.at(predicted, self.springs[:, 0], delta_0)
            np.add.at(predicted, self.springs[:, 1], -delta_1)

        # Floor collision
        below = predicted[:, 1] < floor_y
        predicted[below, 1] = floor_y

        # Update velocity from position change
        vels = (predicted - verts) / dt
        verts[:] = predicted

        self.vertices = verts
        self.velocities = vels
        self.position = np.mean(self.vertices, axis=0)
        self._compute_normals()
        self._compute_aabb()

    def apply_force_at_point(self, point: np.ndarray, force: np.ndarray,
                             radius: float = 0.3):
        """Apply force to vertices within radius of point.

        Used by probe PUSH mode. Force is scaled by distance falloff.

        Args:
            point: World-space point to apply force at.
            force: Force vector to apply.
            radius: Influence radius.
        """
        diffs = self.vertices - point[None, :]
        dists = np.linalg.norm(diffs, axis=1)
        mask = dists < radius

        if not np.any(mask):
            return

        # Distance-based falloff (linear)
        weights = 1.0 - dists[mask] / radius
        self.velocities[mask] += force[None, :] * weights[:, None] / self.masses[mask, None]

    def translate(self, delta: np.ndarray) -> None:
        """Translate all vertices by delta."""
        delta = np.asarray(delta, dtype=np.float64)
        self.vertices += delta
        self.rest_vertices += delta
        self.position += delta
        self.aabb_min += delta
        self.aabb_max += delta

    def scale(self, factor: float, pivot: Optional[np.ndarray] = None) -> None:
        """Scale about a pivot point (default: centroid)."""
        if pivot is None:
            pivot = self.position.copy()
        pivot = np.asarray(pivot, dtype=np.float64)
        self.vertices = pivot + factor * (self.vertices - pivot)
        self.rest_vertices = pivot + factor * (self.rest_vertices - pivot)
        self.position = pivot + factor * (self.position - pivot)
        self.build_spring_network()
        self._compute_aabb()

    def rotate(self, axis: np.ndarray, angle_deg: float,
               pivot: Optional[np.ndarray] = None) -> None:
        """Rotate about an axis through a pivot point using Rodrigues' formula."""
        if pivot is None:
            pivot = self.position.copy()
        pivot = np.asarray(pivot, dtype=np.float64)
        axis = np.asarray(axis, dtype=np.float64)
        axis = axis / (np.linalg.norm(axis) + 1e-10)

        theta = np.radians(angle_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        for arr in [self.vertices, self.rest_vertices]:
            centered = arr - pivot
            dot = np.sum(centered * axis, axis=1, keepdims=True)
            cross = np.cross(centered, axis)
            rotated = centered * cos_t - cross * sin_t + axis * dot * (1 - cos_t)
            arr[:] = rotated + pivot

        self.position = np.mean(self.vertices, axis=0)
        self.build_spring_network()
        self._compute_normals()
        self._compute_aabb()

    def _compute_normals(self) -> None:
        """Compute per-face normals via cross product."""
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

    def get_state(self) -> dict:
        """Serialize for WebSocket / Three.js consumption."""
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
            "body_type": self.body_type,
            "solver": self.solver,
            "spring_count": len(self.springs),
            "vertex_count": len(self.vertices),
        }
