"""
Wavefront OBJ file parser for loading 3D triangle meshes.

===== OBJ FILE FORMAT =====

The Wavefront OBJ format is a simple text-based geometry format.
Each line begins with a keyword followed by data:

    v  x y z          -- Vertex position (3 floats)
    vn nx ny nz       -- Vertex normal   (3 floats)
    vt u v            -- Texture coordinate (2 floats)
    f  v1 v2 v3 ...   -- Face (indices, 1-based)

Face indices may include normal/texture references:
    f  v1//n1 v2//n2 v3//n3
    f  v1/t1/n1 v2/t2/n2 v3/t3/n3

Polygons with more than 3 vertices are triangulated by fan
decomposition from the first vertex.

===== TRIANGULATION =====

For a polygon with vertices [v0, v1, v2, ..., vN]:
    Triangle 0: (v0, v1, v2)
    Triangle 1: (v0, v2, v3)
    ...
    Triangle N-2: (v0, vN-1, vN)

This simple fan triangulation works correctly for convex polygons,
which is the common case in OBJ files exported from modelling tools.

===== COMPATIBILITY =====

This parser is designed to replace the original C++ ``Cargador.cpp``
loader from the 2008 UDEC Haptic SIM project.  That loader parsed
``v`` and ``f`` lines only (no normals or textures) and stored
results in raw float/int arrays.  This module returns structured
numpy arrays suitable for the :class:`RigidBody` constructor.

===== REFERENCES =====

- Wavefront OBJ specification, Silicon Graphics (1995)
- Original C++ Cargador.cpp / Cargador.h from UDEC Haptic SIM (2008)
"""
import os
import numpy as np
from typing import Tuple, Optional

from .rigid_body import RigidBody


def parse_face_index(token: str) -> int:
    """Parse one face vertex token and return the 0-based vertex index.

    Handles formats:
        ``v``
        ``v/vt``
        ``v/vt/vn``
        ``v//vn``

    OBJ indices are 1-based; this function converts to 0-based.
    Negative indices (relative to end of list) are NOT supported.
    """
    parts = token.split("/")
    return int(parts[0]) - 1


def load_obj(filepath: str, name: Optional[str] = None,
             color: Optional[list] = None) -> RigidBody:
    """Load a Wavefront OBJ file and return a :class:`RigidBody`.

    Parameters
    ----------
    filepath : str
        Path to the ``.obj`` file.
    name : str, optional
        Name for the body.  Defaults to the filename stem.
    color : list[float], optional
        RGBA colour for rendering.

    Returns
    -------
    RigidBody
        A rigid body initialised from the mesh data.

    Raises
    ------
    FileNotFoundError
        If *filepath* does not exist.
    ValueError
        If the file contains no vertices or no faces.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"OBJ file not found: {filepath}")

    vertices = []
    faces = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0]

            if keyword == "v" and len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])

            elif keyword == "f" and len(parts) >= 4:
                indices = [parse_face_index(p) for p in parts[1:]]
                # Fan triangulation for polygons with > 3 vertices
                for i in range(1, len(indices) - 1):
                    faces.append([indices[0], indices[i], indices[i + 1]])

    if not vertices:
        raise ValueError(f"No vertices found in {filepath}")
    if not faces:
        raise ValueError(f"No faces found in {filepath}")

    if name is None:
        name = os.path.splitext(os.path.basename(filepath))[0]

    return RigidBody(
        vertices=np.array(vertices, dtype=np.float64),
        faces=np.array(faces, dtype=np.int32),
        name=name,
        color=color,
    )


# ======================================================================
# Primitive mesh generators (for default scenes / testing)
# ======================================================================

def create_box(
    center: np.ndarray,
    size: float = 1.0,
    name: str = "box",
    color: Optional[list] = None,
) -> RigidBody:
    """Create an axis-aligned box (12 triangles, 8 vertices).

    Parameters
    ----------
    center : array_like
        Centre of the box [x, y, z].
    size : float
        Side length.
    name : str
        Body name.
    color : list[float], optional
        RGBA colour.
    """
    h = size / 2.0
    c = np.asarray(center, dtype=np.float64)
    verts = np.array([
        [-h, -h, -h], [ h, -h, -h], [ h,  h, -h], [-h,  h, -h],
        [-h, -h,  h], [ h, -h,  h], [ h,  h,  h], [-h,  h,  h],
    ]) + c

    faces = np.array([
        # -Z face
        [0, 1, 2], [0, 2, 3],
        # +Z face
        [4, 6, 5], [4, 7, 6],
        # -Y face
        [0, 5, 1], [0, 4, 5],
        # +Y face
        [2, 7, 3], [2, 6, 7],
        # -X face
        [0, 3, 7], [0, 7, 4],
        # +X face
        [1, 5, 6], [1, 6, 2],
    ], dtype=np.int32)

    return RigidBody(verts, faces, name=name, color=color)


def create_sphere(
    center: np.ndarray,
    radius: float = 0.5,
    rings: int = 12,
    sectors: int = 16,
    name: str = "sphere",
    color: Optional[list] = None,
) -> RigidBody:
    """Create a UV-sphere mesh.

    Parameters
    ----------
    center : array_like
        Centre of the sphere.
    radius : float
        Sphere radius.
    rings : int
        Number of latitude rings (vertical subdivisions).
    sectors : int
        Number of longitude sectors (horizontal subdivisions).
    name : str
        Body name.
    color : list[float], optional
        RGBA colour.
    """
    c = np.asarray(center, dtype=np.float64)
    verts = []
    faces = []

    for r in range(rings + 1):
        phi = np.pi * r / rings
        for s in range(sectors + 1):
            theta = 2.0 * np.pi * s / sectors
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.cos(phi)
            z = radius * np.sin(phi) * np.sin(theta)
            verts.append([x + c[0], y + c[1], z + c[2]])

    for r in range(rings):
        for s in range(sectors):
            v0 = r * (sectors + 1) + s
            v1 = v0 + 1
            v2 = v0 + sectors + 1
            v3 = v2 + 1

            if r != 0:
                faces.append([v0, v2, v1])
            if r != rings - 1:
                faces.append([v1, v2, v3])

    return RigidBody(
        np.array(verts, dtype=np.float64),
        np.array(faces, dtype=np.int32),
        name=name,
        color=color,
    )
