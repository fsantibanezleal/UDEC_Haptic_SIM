"""
Scene manager for the 3D haptic simulation.

===== ARCHITECTURE =====

The Scene orchestrates all simulation computation in the backend:
    1. Body management (add/remove/transform)
    2. Spatial structure-based collision detection (AABB/OBB/Octree/BVH)
    3. Nearest surface query (vectorized centroid + top-K detail)
    4. Spring-damper force feedback
    5. Deformable body physics (MSD/XPBD)
    6. Probe interaction modes (free/grab/push)
    7. State serialization for the frontend

All heavy computation uses NumPy vectorized operations.
The frontend only renders and captures user input.

References:
    - Original C++ BigBangT.cpp from UDEC Haptic SIM (2008)
"""
import numpy as np
from typing import Optional, List, Dict, Union

from .rigid_body import RigidBody
from .deformable import DeformableBody
from .collision import (
    detect_all_collisions,
    find_nearest_surface_vectorized,
    MeshCollisionData,
    create_spatial_structure,
)
from .spatial import SPATIAL_METHODS
from .physics import SpringForceModel
from .obj_loader import create_box, create_sphere
from .probe_modes import ProbeController


class Scene:
    """Top-level simulation scene manager."""

    def __init__(self, contact_threshold: float = 0.3):
        self.bodies: List[Union[RigidBody, DeformableBody]] = []
        self.force_model = SpringForceModel()
        self.contact_threshold = contact_threshold

        # Probe state
        self.probe_position = np.array([0.0, 0.0, 2.0])
        self.probe_velocity = np.zeros(3)
        self._prev_probe = self.probe_position.copy()

        # Probe controller
        self.probe_controller = ProbeController()

        # Spatial structure
        self.spatial_method = 'aabb'
        self.spatial_structure = create_spatial_structure('aabb')
        self.spatial_max_depth = 6
        self.show_spatial_viz = False

        # Collision state (recomputed when bodies move)
        self._collision_data: List[MeshCollisionData] = []
        self.collision_pairs: list = []
        self._bodies_dirty = True

        # Cached state for fast GET
        self._cached_state: Optional[Dict] = None

        # UI toggles
        self.show_octree = False

    # ------------------------------------------------------------------
    # Spatial method management
    # ------------------------------------------------------------------

    def set_spatial_method(self, method: str) -> None:
        """Change the spatial acceleration structure.

        Args:
            method: One of 'aabb', 'obb', 'octree', 'bvh'.
        """
        if method not in SPATIAL_METHODS:
            return
        self.spatial_method = method
        self.spatial_structure = create_spatial_structure(method)
        self._bodies_dirty = True

    # ------------------------------------------------------------------
    # Body management
    # ------------------------------------------------------------------

    def add_body(self, body: Union[RigidBody, DeformableBody]) -> int:
        """Add a body to the scene."""
        self.bodies.append(body)
        self._bodies_dirty = True
        return len(self.bodies) - 1

    def remove_body(self, index: int) -> None:
        """Remove a body by index."""
        if 0 <= index < len(self.bodies):
            self.bodies.pop(index)
            self._bodies_dirty = True

    def clear(self) -> None:
        """Remove all bodies and reset state."""
        self.bodies.clear()
        self.collision_pairs.clear()
        self._collision_data.clear()
        self.force_model.release()
        self.probe_controller = ProbeController()
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

    def make_body_deformable(self, index: int, mass: float = 1.0,
                             stiffness: float = 500.0, damping: float = 5.0,
                             solver: str = "msd") -> bool:
        """Convert a rigid body to deformable.

        Args:
            index: Body index to convert.
            mass: Per-vertex mass.
            stiffness: Spring stiffness.
            damping: Spring damping.
            solver: "msd" or "xpbd".

        Returns:
            True if conversion succeeded.
        """
        if index < 0 or index >= len(self.bodies):
            return False

        body = self.bodies[index]
        if isinstance(body, DeformableBody):
            return False  # already deformable

        deformable = DeformableBody.from_rigid_body(
            body, mass=mass, stiffness=stiffness, damping=damping, solver=solver
        )
        self.bodies[index] = deformable
        self._bodies_dirty = True
        return True

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------

    def step(self, dt: float = 1.0 / 60.0) -> Dict:
        """Run one simulation step.

        1. Step deformable bodies (MSD/XPBD).
        2. Rebuild spatial structure if bodies dirty.
        3. Probe interaction.
        4. Nearest surface + force computation.
        """
        # Probe velocity
        self.probe_velocity = (self.probe_position - self._prev_probe) / max(dt, 1e-6)
        self._prev_probe = self.probe_position.copy()

        force = np.zeros(3)

        if self.bodies:
            # Step 1: Deformable body physics
            for body in self.bodies:
                if isinstance(body, DeformableBody):
                    if body.solver == 'xpbd':
                        body.step_xpbd(dt=dt)
                    else:
                        body.step_msd(dt=dt)
                    self._bodies_dirty = True

            # Step 2: Rebuild spatial structure if dirty
            if self._bodies_dirty:
                self.spatial_structure.build(self.bodies)
                self.collision_pairs = self.spatial_structure.query_collisions()

                for body in self.bodies:
                    body.collision_faces.clear()
                for bi, fi, bj, fj in self.collision_pairs:
                    if bi < len(self.bodies):
                        self.bodies[bi].collision_faces.add(int(fi))
                    if bj < len(self.bodies):
                        self.bodies[bj].collision_faces.add(int(fj))

                self._bodies_dirty = False

            # Step 3: Probe interaction
            self.probe_controller.update(self.probe_position, self)

            # Step 4: Nearest surface (vectorized)
            nearest_pt, nearest_dist = self.spatial_structure.query_nearest(
                self.probe_position, top_k=5
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
        """Update the probe position."""
        self.probe_position = np.asarray(position, dtype=np.float64)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def get_state(self, force: Optional[np.ndarray] = None) -> Dict:
        """Get cached or fresh state."""
        if self._cached_state is not None:
            return self._cached_state
        f = force if force is not None else np.zeros(3)
        return self._build_state(f)

    def _build_state(self, force: np.ndarray) -> Dict:
        """Build the full state dict for the frontend."""
        spatial_viz = []
        if self.show_spatial_viz:
            try:
                spatial_viz = self.spatial_structure.get_viz_data(self.spatial_max_depth)
            except Exception:
                pass

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
            "spatial_method": self.spatial_method,
            "spatial_viz": spatial_viz,
            "probe_mode": self.probe_controller.mode,
            "probe_controller": self.probe_controller.get_state(),
        }
        return state
