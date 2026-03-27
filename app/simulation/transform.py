"""
3D transformation utilities for the haptic simulation.

===== RODRIGUES' ROTATION FORMULA =====

Given a unit rotation axis k and angle theta, a vector v is rotated as:

    v_rot = v*cos(t) + (k x v)*sin(t) + k*(k . v)*(1 - cos(t))

This is equivalent to multiplying by the rotation matrix R(k, t).

===== ROTATION MATRICES =====

Elementary rotations about the coordinate axes:

    Rx(t) = [[1,    0,     0   ],
             [0,  cos(t), -sin(t)],
             [0,  sin(t),  cos(t)]]

    Ry(t) = [[ cos(t), 0, sin(t)],
             [ 0,      1, 0     ],
             [-sin(t), 0, cos(t)]]

    Rz(t) = [[cos(t), -sin(t), 0],
             [sin(t),  cos(t), 0],
             [0,       0,      1]]

===== HOMOGENEOUS COORDINATES =====

A 4x4 homogeneous transformation matrix combines rotation R and
translation t:

    T = [[R, t],
         [0, 1]]

Applying: p' = T @ [p; 1]

===== QUATERNION OPERATIONS =====

A unit quaternion q = (w, x, y, z) encodes a rotation of angle t
about axis k as:

    q = (cos(t/2),  sin(t/2)*kx,  sin(t/2)*ky,  sin(t/2)*kz)

Quaternion multiplication (Hamilton product):
    q1 * q2 = (w1*w2 - v1.v2,  w1*v2 + w2*v1 + v1 x v2)

Quaternions avoid gimbal lock and are efficient for composing
rotations.

===== REFERENCES =====

- Rodrigues (1840), Des lois geometriques qui regissent les
  deplacements d'un systeme solide
- Shoemake (1985), Animating rotation with quaternion curves, SIGGRAPH
- Diebel (2006), Representing Attitude: Euler Angles, Unit
  Quaternions, and Rotation Vectors, Stanford TR
"""
import numpy as np
from typing import Optional


# ======================================================================
# Rodrigues rotation
# ======================================================================

def rodrigues_rotation(
    vectors: np.ndarray,
    axis: np.ndarray,
    angle_deg: float,
) -> np.ndarray:
    """Rotate an array of 3D vectors using Rodrigues' formula.

    Parameters
    ----------
    vectors : np.ndarray, shape (N, 3) or (3,)
        Points or vectors to rotate.
    axis : np.ndarray, shape (3,)
        Rotation axis (will be normalised).
    angle_deg : float
        Rotation angle in degrees.

    Returns
    -------
    np.ndarray
        Rotated vectors, same shape as *vectors*.
    """
    k = np.asarray(axis, dtype=np.float64)
    k = k / (np.linalg.norm(k) + 1e-12)
    t = np.radians(angle_deg)
    cos_t = np.cos(t)
    sin_t = np.sin(t)

    v = np.atleast_2d(vectors)
    dot = np.sum(v * k, axis=1, keepdims=True)
    cross = np.cross(v, k)
    result = v * cos_t - cross * sin_t + k * dot * (1 - cos_t)

    if vectors.ndim == 1:
        return result[0]
    return result


# ======================================================================
# Elementary rotation matrices
# ======================================================================

def rotation_matrix_x(angle_deg: float) -> np.ndarray:
    """3x3 rotation matrix about the X axis."""
    t = np.radians(angle_deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [1, 0,  0],
        [0, c, -s],
        [0, s,  c],
    ])


def rotation_matrix_y(angle_deg: float) -> np.ndarray:
    """3x3 rotation matrix about the Y axis."""
    t = np.radians(angle_deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [ c, 0, s],
        [ 0, 1, 0],
        [-s, 0, c],
    ])


def rotation_matrix_z(angle_deg: float) -> np.ndarray:
    """3x3 rotation matrix about the Z axis."""
    t = np.radians(angle_deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1],
    ])


def rotation_matrix_axis(axis: np.ndarray, angle_deg: float) -> np.ndarray:
    """3x3 rotation matrix about an arbitrary axis (Rodrigues).

    Parameters
    ----------
    axis : array_like, shape (3,)
        Rotation axis.
    angle_deg : float
        Angle in degrees.
    """
    k = np.asarray(axis, dtype=np.float64)
    k = k / (np.linalg.norm(k) + 1e-12)
    t = np.radians(angle_deg)
    c, s = np.cos(t), np.sin(t)
    K = np.array([
        [0,    -k[2],  k[1]],
        [k[2],  0,    -k[0]],
        [-k[1], k[0],  0   ],
    ])
    return np.eye(3) * c + (1 - c) * np.outer(k, k) + s * K


# ======================================================================
# Homogeneous transforms
# ======================================================================

def homogeneous_transform(
    rotation: np.ndarray,
    translation: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Build a 4x4 homogeneous transformation matrix.

    Parameters
    ----------
    rotation : np.ndarray, shape (3, 3)
        Rotation matrix.
    translation : np.ndarray, shape (3,), optional
        Translation vector.  Default is zero.
    """
    T = np.eye(4)
    T[:3, :3] = rotation
    if translation is not None:
        T[:3, 3] = np.asarray(translation)
    return T


def apply_homogeneous(
    T: np.ndarray,
    points: np.ndarray,
) -> np.ndarray:
    """Apply a 4x4 homogeneous transform to an (N, 3) array of points.

    Appends a homogeneous coordinate w=1, multiplies, and strips w.
    """
    pts = np.atleast_2d(points)
    ones = np.ones((pts.shape[0], 1))
    homo = np.hstack([pts, ones])
    result = (T @ homo.T).T
    out = result[:, :3]
    if points.ndim == 1:
        return out[0]
    return out


# ======================================================================
# Quaternion operations
# ======================================================================

def quat_from_axis_angle(axis: np.ndarray, angle_deg: float) -> np.ndarray:
    """Create a unit quaternion from an axis-angle representation.

    Returns
    -------
    np.ndarray, shape (4,)
        Quaternion as [w, x, y, z].
    """
    k = np.asarray(axis, dtype=np.float64)
    k = k / (np.linalg.norm(k) + 1e-12)
    half = np.radians(angle_deg) / 2.0
    return np.array([np.cos(half), *(np.sin(half) * k)])


def quat_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product of two quaternions [w, x, y, z]."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def quat_to_matrix(q: np.ndarray) -> np.ndarray:
    """Convert a unit quaternion [w, x, y, z] to a 3x3 rotation matrix."""
    w, x, y, z = q / (np.linalg.norm(q) + 1e-12)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z),     2 * (x * z + w * y)],
        [2 * (x * y + w * z),     1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y),     2 * (y * z + w * x),     1 - 2 * (x * x + y * y)],
    ])


def quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate a 3D vector *v* by unit quaternion *q*.

    Uses the formula: v' = q * (0, v) * q_conj.
    """
    R = quat_to_matrix(q)
    return R @ np.asarray(v)
