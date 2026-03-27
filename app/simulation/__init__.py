"""
Simulation engine for 3D haptic interaction.

Provides rigid body management, vectorized hierarchical collision
detection (AABB broad + batch filter), spring-based force computation,
and OBJ mesh loading.
"""

from .rigid_body import RigidBody
from .collision import (
    detect_all_collisions,
    find_nearest_surface_vectorized,
    AABB,
)
from .physics import SpringForceModel
from .obj_loader import load_obj
from .scene import Scene
from .transform import (
    rodrigues_rotation,
    rotation_matrix_x,
    rotation_matrix_y,
    rotation_matrix_z,
    homogeneous_transform,
)

__all__ = [
    "RigidBody",
    "detect_all_collisions",
    "find_nearest_surface_vectorized",
    "AABB",
    "SpringForceModel",
    "load_obj",
    "Scene",
    "rodrigues_rotation",
    "rotation_matrix_x",
    "rotation_matrix_y",
    "rotation_matrix_z",
    "homogeneous_transform",
]
