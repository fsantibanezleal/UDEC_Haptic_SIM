"""
Spatial acceleration structures for collision detection and nearest queries.

Provides multiple spatial indexing methods:
    - AABB Tree: Axis-aligned bounding box hierarchy (default)
    - OBB Tree: Oriented bounding box with PCA axes
    - Octree: Recursive 8-child spatial subdivision
    - BVH: Binary bounding volume hierarchy
"""
from .base import SpatialStructure
from .aabb_tree import AABBTree
from .obb import OBBTree
from .octree import Octree
from .bvh import BVH

SPATIAL_METHODS = {
    'aabb': AABBTree,
    'obb': OBBTree,
    'octree': Octree,
    'bvh': BVH,
}

__all__ = [
    'SpatialStructure',
    'AABBTree',
    'OBBTree',
    'Octree',
    'BVH',
    'SPATIAL_METHODS',
]
