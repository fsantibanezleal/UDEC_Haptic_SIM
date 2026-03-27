"""
Abstract base class for spatial acceleration structures.

All spatial structures implement the same interface for building,
querying collisions, finding nearest surfaces, and producing
visualization data for the frontend.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class SpatialStructure(ABC):
    """Abstract spatial acceleration structure for collision and proximity queries."""

    @abstractmethod
    def build(self, bodies) -> None:
        """Build or rebuild the spatial structure from a list of bodies.

        Args:
            bodies: List of RigidBody or DeformableBody instances.
        """

    @abstractmethod
    def query_collisions(self) -> List[Tuple[int, int, int, int]]:
        """Find all colliding triangle pairs across all bodies.

        Returns:
            List of (body_a_idx, face_a_idx, body_b_idx, face_b_idx) tuples.
        """

    @abstractmethod
    def query_nearest(self, probe: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, float]:
        """Find the nearest surface point to the probe.

        Args:
            probe: Query point (3,).
            top_k: Number of candidate triangles for detailed test.

        Returns:
            (nearest_point, distance) tuple.
        """

    @abstractmethod
    def get_viz_data(self, max_depth: int = 6) -> List[dict]:
        """Get visualization data for the spatial structure.

        Args:
            max_depth: Maximum depth of nodes to include.

        Returns:
            List of dicts with visualization info (type, center, size, etc.)
        """
