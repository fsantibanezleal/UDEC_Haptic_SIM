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
from pathlib import Path
import numpy as np
from typing import Tuple, Optional, List

from .rigid_body import RigidBody

# Directory for built-in OBJ models
_MODELS_DIR = Path(__file__).parent.parent / "static" / "models"


def parse_face_index(token: str) -> Tuple[int, int, int]:
    """Parse one face vertex token and return 0-based indices.

    Handles formats:
        ``v``            -> (v, -1, -1)
        ``v/vt``         -> (v, vt, -1)
        ``v/vt/vn``      -> (v, vt, vn)
        ``v//vn``        -> (v, -1, vn)

    OBJ indices are 1-based; this function converts to 0-based.
    Returns -1 for absent texture or normal indices.
    Negative indices (relative to end of list) are NOT supported.
    """
    parts = token.split("/")
    vi = int(parts[0]) - 1
    ti = int(parts[1]) - 1 if len(parts) > 1 and parts[1] != "" else -1
    ni = int(parts[2]) - 1 if len(parts) > 2 and parts[2] != "" else -1
    return vi, ti, ni


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
    tex_coords = []
    file_normals = []
    faces = []
    face_tex_indices = []
    face_normal_indices = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0]

            if keyword == "v" and len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])

            elif keyword == "vt" and len(parts) >= 3:
                tex_coords.append([float(parts[1]), float(parts[2])])

            elif keyword == "vn" and len(parts) >= 4:
                file_normals.append([float(parts[1]), float(parts[2]), float(parts[3])])

            elif keyword == "f" and len(parts) >= 4:
                parsed = [parse_face_index(p) for p in parts[1:]]
                v_indices = [p[0] for p in parsed]
                t_indices = [p[1] for p in parsed]
                n_indices = [p[2] for p in parsed]
                # Fan triangulation for polygons with > 3 vertices
                for i in range(1, len(v_indices) - 1):
                    faces.append([v_indices[0], v_indices[i], v_indices[i + 1]])
                    face_tex_indices.append([t_indices[0], t_indices[i], t_indices[i + 1]])
                    face_normal_indices.append([n_indices[0], n_indices[i], n_indices[i + 1]])

    if not vertices:
        raise ValueError(f"No vertices found in {filepath}")
    if not faces:
        raise ValueError(f"No faces found in {filepath}")

    if name is None:
        name = os.path.splitext(os.path.basename(filepath))[0]

    body = RigidBody(
        vertices=np.array(vertices, dtype=np.float64),
        faces=np.array(faces, dtype=np.int32),
        name=name,
        color=color,
    )

    # Attach texture coordinates if present
    if tex_coords:
        body.tex_coords = np.array(tex_coords, dtype=np.float64)
        body.has_texture = True

    # Attach file normals if present (per-vertex normals from OBJ)
    if file_normals:
        body.file_normals = np.array(file_normals, dtype=np.float64)

    return body


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


def create_torus(
    center: np.ndarray,
    major_r: float = 0.5,
    minor_r: float = 0.2,
    rings: int = 16,
    sectors: int = 16,
    name: str = "torus",
    color: Optional[list] = None,
) -> RigidBody:
    """Create a parametric torus mesh.

    Parameters
    ----------
    center : array_like
        Centre of the torus [x, y, z].
    major_r : float
        Major radius (distance from center of tube to center of torus).
    minor_r : float
        Minor radius (radius of the tube).
    rings : int
        Number of rings around the torus.
    sectors : int
        Number of sectors in each ring cross-section.
    name : str
        Body name.
    color : list[float], optional
        RGBA colour.
    """
    c = np.asarray(center, dtype=np.float64)
    verts = []
    faces = []

    for i in range(rings):
        theta = 2.0 * np.pi * i / rings
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        for j in range(sectors):
            phi = 2.0 * np.pi * j / sectors
            cos_p = np.cos(phi)
            sin_p = np.sin(phi)

            x = (major_r + minor_r * cos_p) * cos_t
            y = minor_r * sin_p
            z = (major_r + minor_r * cos_p) * sin_t
            verts.append([x + c[0], y + c[1], z + c[2]])

    for i in range(rings):
        for j in range(sectors):
            v0 = i * sectors + j
            v1 = i * sectors + (j + 1) % sectors
            v2 = ((i + 1) % rings) * sectors + j
            v3 = ((i + 1) % rings) * sectors + (j + 1) % sectors

            faces.append([v0, v2, v1])
            faces.append([v1, v2, v3])

    return RigidBody(
        np.array(verts, dtype=np.float64),
        np.array(faces, dtype=np.int32),
        name=name,
        color=color,
    )


def load_builtin(
    model_name: str,
    name: Optional[str] = None,
    color: Optional[list] = None,
) -> RigidBody:
    """Load a built-in OBJ model from the models directory.

    Parameters
    ----------
    model_name : str
        Name of the model (e.g., "bunny", "teapot").
    name : str, optional
        Override name for the body.
    color : list[float], optional
        RGBA colour.

    Returns
    -------
    RigidBody
        Loaded model as a rigid body.
    """
    filepath = _MODELS_DIR / f"{model_name}.obj"
    if not filepath.is_file():
        raise FileNotFoundError(f"Built-in model not found: {filepath}")
    return load_obj(str(filepath), name=name or model_name, color=color)


def list_builtin_models() -> List[str]:
    """List available built-in OBJ model names.

    Returns
    -------
    list[str]
        Names of available models (without .obj extension).
    """
    if not _MODELS_DIR.is_dir():
        return []
    return sorted(
        p.stem for p in _MODELS_DIR.glob("*.obj") if p.is_file()
    )
