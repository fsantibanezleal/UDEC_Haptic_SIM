"""
Scene manager for the 3D haptic simulation.

===== ARCHITECTURE =====

The Scene orchestrates all simulation computation in the backend:
    1. Body management (add/remove/transform)
    2. Hierarchical collision detection (AABB broad + batch filter)
    3. Nearest surface query (vectorized centroid + top-K detail)
    4. Spring-damper force feedback
    5. State serialization for the frontend

All heavy computation uses NumPy vectorized operations.
The frontend only renders and captures user input.

References:
    - Original C++ BigBangT.cpp from UDEC Haptic SIM (2008)
"""
import numpy as np
from typing import Optional, List, Dict

from .rigid_body import RigidBody
from .collision import (
    detect_all_collisions,
    find_nearest_surface_vectorized,
    MeshCollisionData,
)
from .physics import SpringForceModel
from .obj_loader import create_box, create_sphere


class Scene:
    """Top-level simulation scene manager."""

    def __init__(self, contact_threshold: float = 0.3):
        self.bodies: List[RigidBody] = []
        self.force_model = SpringForceModel()
        self.contact_threshold = contact_threshold

        # Probe state
        self.probe_position = np.array([0.0, 0.0, 2.0])
        self.probe_velocity = np.zeros(3)
        self._prev_probe = self.probe_position.copy()

        # Collision state (recomputed when bodies move)
        self._collision_data: List[MeshCollisionData] = []
        self.collision_pairs: list = []
        self._bodies_dirty = True

        # Cached state for fast GET
        self._cached_state: Optional[Dict] = None

        # UI toggles
        self.show_octree = False

    # ------------------------------------------------------------------
    # Body management
    # ------------------------------------------------------------------

    def add_body(self, body: RigidBody) -> int:
        self.bodies.append(body)
        self._bodies_dirty = True
        return len(self.bodies) - 1

    def remove_body(self, index: int) -> None:
        if 0 <= index < len(self.bodies):
            self.bodies.pop(index)
            self._bodies_dirty = True

    def clear(self) -> None:
        self.bodies.clear()
        self.collision_pairs.clear()
        self._collision_data.clear()
        self.force_model.release()
        self._bodies_dirty = True

    def mark_bodies_dirty(self) -> None:
        """Call after any body transform to trigger collision recompute."""
        self._bodies_dirty = True

    def load_default_scene(self) -> None:
        """Create demo scene: two overlapping cubes + sphere."""
        self.clear()
        self.add_body(create_box(
            center=np.array([-0.3, 0.0, 0.0]), size=1.0,
            name="Cube A", color=[0.3, 0.5, 0.9, 1.0]))
        self.add_body(create_box(
            center=np.array([0.5, 0.0, 0.0]), size=1.0,
            name="Cube B", color=[0.9, 0.5, 0.3, 1.0]))
        self.add_body(create_sphere(
            center=np.array([0.0, 1.5, 0.0]), radius=0.5,
            rings=10, sectors=14, name="Sphere", color=[0.4, 0.8, 0.4, 1.0]))
        self._bodies_dirty = True

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------

    def step(self, dt: float = 1.0 / 60.0) -> Dict:
        """Run one simulation step.

        Collision detection only runs when bodies have moved.
        Nearest-surface and force run every step (fast, vectorized).
        """
        # Probe velocity
        self.probe_velocity = (self.probe_position - self._prev_probe) / max(dt, 1e-6)
        self._prev_probe = self.probe_position.copy()

        force = np.zeros(3)

        if self.bodies:
            # Collision: only recompute when bodies moved
            if self._bodies_dirty:
                self._collision_data, self.collision_pairs = \
                    detect_all_collisions(self.bodies)

                for body in self.bodies:
                    body.collision_faces.clear()
                for bi, fi, bj, fj in self.collision_pairs:
                    self.bodies[bi].collision_faces.add(int(fi))
                    self.bodies[bj].collision_faces.add(int(fj))

                self._bodies_dirty = False

            # Nearest surface (vectorized: centroid batch + top-K detail)
            nearest_pt, nearest_dist = find_nearest_surface_vectorized(
                self.probe_position, self._collision_data, top_k=5
            )

            if nearest_dist < self.contact_threshold:
                self.force_model.set_anchor(nearest_pt)
            else:
                self.force_model.release()

            force = self.force_model.compute_force(
                self.probe_position, self.probe_velocity
            )

        self._cached_state = self._build_state(force)
        return self._cached_state

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------

    def set_probe_position(self, position: np.ndarray) -> None:
        self.probe_position = np.asarray(position, dtype=np.float64)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def get_state(self, force: Optional[np.ndarray] = None) -> Dict:
        if self._cached_state is not None:
            return self._cached_state
        f = force if force is not None else np.zeros(3)
        return self._build_state(f)

    def _build_state(self, force: np.ndarray) -> Dict:
        state = {
            "bodies": [b.get_state() for b in self.bodies],
            "probe": {
                "position": self.probe_position.tolist(),
                "velocity": self.probe_velocity.tolist(),
            },
            "force": {
                "vector": force.tolist(),
                "magnitude": float(np.linalg.norm(force)),
                **self.force_model.get_state(),
            },
            "collision_count": len(self.collision_pairs),
        }
        return state
