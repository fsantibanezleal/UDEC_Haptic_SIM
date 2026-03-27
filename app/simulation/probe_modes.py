"""
Probe interaction modes for the haptic simulation.

Supports three modes:
    - Free: Probe moves independently, only sensing forces.
    - Grab: Probe grabs the nearest body and drags it.
    - Push: Probe pushes vertices of deformable bodies within a radius.

References:
    - Zilles & Salisbury (1995), A Constraint-Based God-Object Method For
      Haptic Display
"""
import numpy as np
from typing import Optional


class ProbeController:
    """Controls probe interaction mode and behavior."""

    def __init__(self):
        self.mode: str = "free"
        self.grabbed_body_index: Optional[int] = None
        self.grab_offset: Optional[np.ndarray] = None
        self.push_radius: float = 0.3
        self.push_strength: float = 0.5

    def set_mode(self, mode: str, scene) -> None:
        """Set the probe interaction mode.

        Args:
            mode: One of "free", "grab", "push".
            scene: The Scene instance (for releasing grabs, etc.)
        """
        if mode == self.mode:
            return

        # Release any active grab
        if self.mode == "grab":
            self.grabbed_body_index = None
            self.grab_offset = None

        self.mode = mode

        # Initialize grab if switching to grab mode
        if mode == "grab" and scene is not None and len(scene.bodies) > 0:
            self._init_grab(scene.probe_position, scene)

    def _init_grab(self, probe_pos: np.ndarray, scene) -> None:
        """Find and grab the nearest body.

        Args:
            probe_pos: Current probe position.
            scene: The Scene instance.
        """
        best_dist = float('inf')
        best_idx = None

        for i, body in enumerate(scene.bodies):
            dist = np.linalg.norm(body.position - probe_pos)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx is not None:
            self.grabbed_body_index = best_idx
            self.grab_offset = scene.bodies[best_idx].position - probe_pos

    def update(self, probe_pos: np.ndarray, scene) -> None:
        """Update probe interaction for the current frame.

        Args:
            probe_pos: Current probe position.
            scene: The Scene instance.
        """
        if self.mode == "grab":
            self._update_grab(probe_pos, scene)
        elif self.mode == "push":
            self._update_push(probe_pos, scene)
        # "free" mode does nothing

    def _update_grab(self, probe_pos: np.ndarray, scene) -> None:
        """Move the grabbed body to follow the probe.

        Args:
            probe_pos: Current probe position.
            scene: The Scene instance.
        """
        if self.grabbed_body_index is None or self.grab_offset is None:
            return

        idx = self.grabbed_body_index
        if idx >= len(scene.bodies):
            self.grabbed_body_index = None
            self.grab_offset = None
            return

        body = scene.bodies[idx]
        target = probe_pos + self.grab_offset
        delta = target - body.position
        body.translate(delta)
        scene._bodies_dirty = True

    def _update_push(self, probe_pos: np.ndarray, scene) -> None:
        """Push vertices of deformable bodies near the probe.

        Args:
            probe_pos: Current probe position.
            scene: The Scene instance.
        """
        from .deformable import DeformableBody

        for body in scene.bodies:
            if not isinstance(body, DeformableBody):
                continue

            # Compute displacement direction (outward from probe)
            diffs = body.vertices - probe_pos[None, :]
            dists = np.linalg.norm(diffs, axis=1)
            mask = dists < self.push_radius

            if not np.any(mask):
                continue

            # Push direction: away from probe
            push_dirs = diffs[mask] / np.maximum(dists[mask, None], 1e-10)
            weights = 1.0 - dists[mask] / self.push_radius
            displacement = push_dirs * weights[:, None] * self.push_strength * 0.02

            body.vertices[mask] += displacement
            body.velocities[mask] += displacement / (1.0 / 60.0)

            body._compute_normals()
            body._compute_aabb()
            scene._bodies_dirty = True

    def get_state(self) -> dict:
        """Serialize probe controller state."""
        return {
            "mode": self.mode,
            "grabbed_body_index": self.grabbed_body_index,
            "push_radius": self.push_radius,
            "push_strength": self.push_strength,
        }
