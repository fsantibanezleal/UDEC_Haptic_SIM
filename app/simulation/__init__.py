"""
Simulation engine for 3D haptic interaction.

Provides rigid body management, deformable body physics,
multiple spatial acceleration structures (AABB/OBB/Octree/BVH),
vectorized hierarchical collision detection, spring-based force
computation, probe interaction modes, and OBJ mesh loading.
"""

from .rigid_body import RigidBody
from .deformable import DeformableBody
from .collision import (
    detect_all_collisions,
    find_nearest_surface_vectorized,
    AABB,
    create_spatial_structure,
)
from .spatial import SPATIAL_METHODS, SpatialStructure, AABBTree, OBBTree, Octree, BVH
from .physics import SpringForceModel
from .obj_loader import load_obj, create_torus, load_builtin, list_builtin_models
from .scene import Scene
from .probe_modes import ProbeController
from .mesh_cutter import cut_mesh_with_plane, cut_deformable_body
from .scene_generator import generate_random_scene
from .transform import (
    rodrigues_rotation,
    rotation_matrix_x,
    rotation_matrix_y,
    rotation_matrix_z,
    homogeneous_transform,
)

__all__ = [
    "RigidBody",
    "DeformableBody",
    "detect_all_collisions",
    "find_nearest_surface_vectorized",
    "AABB",
    "create_spatial_structure",
    "SPATIAL_METHODS",
    "SpatialStructure",
    "AABBTree",
    "OBBTree",
    "Octree",
    "BVH",
    "SpringForceModel",
    "load_obj",
    "create_torus",
    "load_builtin",
    "list_builtin_models",
    "Scene",
    "ProbeController",
    "cut_mesh_with_plane",
    "cut_deformable_body",
    "generate_random_scene",
    "rodrigues_rotation",
    "rotation_matrix_x",
    "rotation_matrix_y",
    "rotation_matrix_z",
    "homogeneous_transform",
]
