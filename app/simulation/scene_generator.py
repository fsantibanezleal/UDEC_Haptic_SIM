"""
Random scene generator for the haptic simulation.

Generates scenes with a mix of rigid and deformable bodies,
using various built-in models (box, sphere, torus, bunny, teapot).
"""
import numpy as np
from typing import List, Union

from .rigid_body import RigidBody
from .deformable import DeformableBody
from .obj_loader import create_box, create_sphere, create_torus, load_builtin


def generate_random_scene(
    num_bodies: int = 5,
    deformable_fraction: float = 0.3,
) -> List[Union[RigidBody, DeformableBody]]:
    """Generate a random scene with a mix of rigid and deformable bodies.

    Picks random models (box, sphere, torus, bunny, teapot).
    Random positions in [-2, 2]^3 (y offset to be above floor).
    Random scales 0.3-1.0.

    Args:
        num_bodies: Number of bodies to generate.
        deformable_fraction: Fraction of bodies that are deformable.

    Returns:
        List of RigidBody and DeformableBody instances.
    """
    bodies = []
    colors = [
        [0.3, 0.5, 0.9, 1.0],
        [0.9, 0.5, 0.3, 1.0],
        [0.4, 0.8, 0.4, 1.0],
        [0.9, 0.4, 0.7, 1.0],
        [0.5, 0.9, 0.9, 1.0],
        [0.8, 0.8, 0.3, 1.0],
        [0.6, 0.3, 0.9, 1.0],
        [0.9, 0.6, 0.6, 1.0],
    ]

    # Available model types (always available)
    model_types = ['box', 'sphere', 'torus']

    # Check if builtin OBJ models are available
    try:
        from .obj_loader import list_builtin_models
        builtins = list_builtin_models()
        model_types.extend(builtins)
    except Exception:
        pass

    for i in range(num_bodies):
        model_type = model_types[np.random.randint(0, len(model_types))]
        center = np.random.uniform(-1.5, 1.5, size=3)
        center[1] = np.random.uniform(0.0, 2.0)  # above floor
        scale = np.random.uniform(0.3, 0.8)
        color = colors[i % len(colors)]
        name = f"{model_type}_{i}"

        try:
            if model_type == 'box':
                body = create_box(center=center, size=scale, name=name, color=color)
            elif model_type == 'sphere':
                body = create_sphere(center=center, radius=scale * 0.5,
                                     rings=8, sectors=12, name=name, color=color)
            elif model_type == 'torus':
                body = create_torus(center=center, major_r=scale * 0.4,
                                    minor_r=scale * 0.15, name=name, color=color)
            else:
                # Try to load builtin model
                body = load_builtin(model_type, name=name, color=color)
                # Scale and position it
                body.scale(scale * 0.5)
                body.translate(center - body.position)
        except Exception:
            # Fallback to box
            body = create_box(center=center, size=scale, name=name, color=color)

        # Convert some to deformable
        if np.random.random() < deformable_fraction:
            body = DeformableBody.from_rigid_body(
                body, mass=1.0, stiffness=500.0, damping=5.0, solver="msd"
            )

        bodies.append(body)

    return bodies
