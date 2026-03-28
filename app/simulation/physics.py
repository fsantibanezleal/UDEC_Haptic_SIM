"""
Force computation for haptic feedback simulation.

===== SPRING-BASED CONTACT FORCE =====

When the user's probe contacts an object surface, a restoring
force is computed using Hooke's law:

    F = -k * (p_probe - p_contact)

where:
    k          = spring stiffness (N/m or dimensionless in simulation)
    p_probe    = current probe position
    p_contact  = nearest point on surface (the *anchor*)

The force pushes the probe away from the surface, simulating
the sensation of touching a solid object.

===== FORCE CLAMPING =====

Physical haptic devices have maximum continuous force limits
(typically 3.3 N for PHANToM Omni).  We clamp:

    if |F| > F_max:
        F = F_max * F_hat

where F_hat = F / |F| is the unit force direction.

===== DAMPING =====

To prevent oscillations at the contact boundary, a viscous
damping term is added:

    F_total = -k * x - b * v

where b is the damping coefficient and v is the probe velocity.

This models the dashpot element of a Kelvin-Voigt visco-elastic
contact.

===== POINT-TO-TRIANGLE PROJECTION =====

Finding the nearest surface point requires projecting the probe
position onto every triangle of the mesh and keeping the closest.
The projection uses Voronoi-region barycentric coordinates to
handle edge and vertex cases correctly (see Ericson Ch. 5).

===== REFERENCES =====

- Salisbury & Srinivasan (1997), PHANToM-based haptic interaction
- Colgate & Brown (1994), Factors affecting the Z-width of a haptic display
- Ericson (2004), Real-Time Collision Detection, Ch. 5.1.5
- Original C++ Haptico.cpp spring model from UDEC Haptic SIM (2008)
"""
import numpy as np
from typing import Optional, Tuple


class SpringForceModel:
    """Computes haptic feedback forces using a spring-damper model.

    The model is a simple Kelvin-Voigt element: a spring (stiffness *k*)
    in parallel with a dashpot (damping *b*).

    Parameters
    ----------
    stiffness : float
        Spring constant *k* (N/m or dimensionless).
    damping : float
        Viscous damping coefficient *b*.
    max_force : float
        Maximum allowable force magnitude (N).  Forces exceeding this
        value are clamped in magnitude but retain their direction.
    """

    def __init__(
        self,
        stiffness: float = 0.2,
        damping: float = 0.05,
        max_force: float = 3.3,
        friction_coefficient: float = 0.0,
    ):
        self.stiffness = stiffness
        self.damping = damping
        self.max_force = max_force
        self.friction_coefficient = friction_coefficient
        self.anchor: Optional[np.ndarray] = None
        self.is_contacting = False

    def set_anchor(self, position: np.ndarray) -> None:
        """Set the anchor point (nearest surface contact point)."""
        self.anchor = np.array(position, dtype=np.float64)
        self.is_contacting = True

    def release(self) -> None:
        """Release the anchor (probe is no longer in contact)."""
        self.anchor = None
        self.is_contacting = False

    def compute_force(
        self,
        probe_position: np.ndarray,
        probe_velocity: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute the haptic feedback force with optional Coulomb friction.

        ::

            F_total = F_spring + F_damping + F_friction

        where F_friction = -mu * |F_normal| * tangent_velocity_hat

        Friction opposes tangential motion at the contact surface.
        The result is clamped so that ``|F| <= max_force``.

        Parameters
        ----------
        probe_position : np.ndarray
            Current probe position [x, y, z].
        probe_velocity : np.ndarray, optional
            Current probe velocity [vx, vy, vz].

        Returns
        -------
        np.ndarray
            Force vector [Fx, Fy, Fz].
        """
        if self.anchor is None:
            return np.zeros(3)

        displacement = probe_position - self.anchor

        # Normal force (along displacement direction)
        f_normal = -self.stiffness * displacement

        # Damping
        f_damp = np.zeros(3)
        if probe_velocity is not None:
            f_damp = -self.damping * probe_velocity

        force = f_normal + f_damp

        # Coulomb friction (if enabled and we have velocity)
        if self.friction_coefficient > 0 and probe_velocity is not None:
            normal_dir = displacement / (np.linalg.norm(displacement) + 1e-10)
            normal_mag = abs(np.dot(force, normal_dir))

            # Tangential velocity (component perpendicular to normal)
            v_normal = np.dot(probe_velocity, normal_dir) * normal_dir
            v_tangent = probe_velocity - v_normal
            v_tang_mag = np.linalg.norm(v_tangent)

            if v_tang_mag > 1e-6:
                f_friction = -self.friction_coefficient * normal_mag * v_tangent / v_tang_mag
                force += f_friction

        # Clamp
        magnitude = np.linalg.norm(force)
        if magnitude > self.max_force:
            force = force / magnitude * self.max_force

        return force

    def get_state(self) -> dict:
        """Serialise for the frontend."""
        return {
            "is_contacting": self.is_contacting,
            "anchor": self.anchor.tolist() if self.anchor is not None else None,
            "stiffness": self.stiffness,
            "damping": self.damping,
            "max_force": self.max_force,
            "friction_coefficient": self.friction_coefficient,
        }


# ======================================================================
# Surface proximity queries
# ======================================================================

def find_nearest_surface_point(
    probe: np.ndarray, body
) -> Tuple[np.ndarray, int, float]:
    """Find the nearest point on a mesh surface to the probe.

    Uses a fast AABB pre-filter: only tests triangles whose bounding
    box is within 2x the current best distance.  This typically reduces
    the number of expensive closest_point_on_triangle calls from N to
    a small constant.

    Parameters
    ----------
    probe : np.ndarray
        Query point [x, y, z].
    body : RigidBody
        The mesh to query against.

    Returns
    -------
    nearest_point : np.ndarray
        Closest point on the surface.
    face_index : int
        Index of the face containing the closest point.
    distance : float
        Euclidean distance from *probe* to *nearest_point*.
    """
    # Quick AABB rejection: if probe is far from body, skip entirely
    aabb_dist = _point_aabb_distance(probe, body.aabb_min, body.aabb_max)
    if aabb_dist > 5.0:  # far away, not worth checking
        return probe.copy(), -1, aabb_dist

    best_dist = float("inf")
    best_point = probe.copy()
    best_face = -1

    # Pre-compute all face vertex arrays for vectorized access
    faces = body.faces
    verts = body.vertices

    for fi in range(len(faces)):
        # Quick per-face AABB check
        fv = verts[faces[fi]]
        fmin = fv.min(axis=0)
        fmax = fv.max(axis=0)
        # Skip if face AABB is further than current best
        face_aabb_dist = _point_aabb_distance(probe, fmin, fmax)
        if face_aabb_dist > best_dist:
            continue

        point = closest_point_on_triangle(probe, fv[0], fv[1], fv[2])
        dist = np.linalg.norm(probe - point)

        if dist < best_dist:
            best_dist = dist
            best_point = point
            best_face = fi

    return best_point, best_face, best_dist


def _point_aabb_distance(p: np.ndarray, aabb_min: np.ndarray, aabb_max: np.ndarray) -> float:
    """Minimum distance from point to axis-aligned bounding box."""
    clamped = np.clip(p, aabb_min, aabb_max)
    return float(np.linalg.norm(p - clamped))


def closest_point_on_triangle(
    p: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    c: np.ndarray,
) -> np.ndarray:
    """Find the closest point on triangle ABC to point P.

    Uses Voronoi-region barycentric coordinates with edge and vertex
    clamping.  This is the method described in Ericson (2004), section
    5.1.5.  The algorithm classifies P into one of seven Voronoi
    regions of the triangle (3 vertices, 3 edges, 1 interior) and
    computes the projection accordingly.

    Parameters
    ----------
    p, a, b, c : np.ndarray
        3D points.

    Returns
    -------
    np.ndarray
        The closest point on triangle ABC.
    """
    ab = b - a
    ac = c - a
    ap = p - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return a.copy()

    bp = p - b
    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return b.copy()

    cp = p - c
    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return c.copy()

    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        return a + v * ab

    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        return a + w * ac

    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + w * (c - b)

    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return a + ab * v + ac * w
