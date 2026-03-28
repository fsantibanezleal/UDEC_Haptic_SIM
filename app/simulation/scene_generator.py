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


def generate_demo_scene(demo_name: str) -> List[Union[RigidBody, DeformableBody]]:
    """Generate a preset demo scene.

    Args:
        demo_name: One of:
            'falling_objects' -- large rigid floor + small objects falling
            'deformable_floor' -- large deformable cube + objects falling
            'rigid_collisions' -- rigid objects colliding
            'deformable_collisions' -- deformable objects colliding and deforming
            'mixed' -- rigid floor, deformable blob, rigid projectiles
    """
    bodies: List[Union[RigidBody, DeformableBody]] = []

    if demo_name == 'falling_objects':
        # Large flat rigid floor (create a big box and flatten Y vertices)
        floor = create_box(center=np.array([0.0, -2.0, 0.0]), size=4.0,
                           name="Floor", color=[0.4, 0.4, 0.5, 1.0])
        # Flatten: compress Y coordinates toward center
        cy = floor.position[1]
        floor.vertices[:, 1] = cy + (floor.vertices[:, 1] - cy) * 0.1
        floor.aabb_min = np.min(floor.vertices, axis=0)
        floor.aabb_max = np.max(floor.vertices, axis=0)
        bodies.append(floor)

        # Small falling objects at various heights
        for i in range(5):
            x = np.random.uniform(-1.5, 1.5)
            y = 1.0 + i * 0.8
            z = np.random.uniform(-1.5, 1.5)
            if i % 2 == 0:
                obj = create_sphere(center=np.array([x, y, z]), radius=0.25,
                                    rings=6, sectors=8, name=f"Ball_{i}",
                                    color=[0.8, 0.3, 0.2, 1.0])
            else:
                obj = create_box(center=np.array([x, y, z]), size=0.4,
                                 name=f"Box_{i}", color=[0.2, 0.5, 0.8, 1.0])
            bodies.append(obj)

    elif demo_name == 'deformable_floor':
        # Large deformable cube as floor
        floor = create_box(center=np.array([0.0, -1.5, 0.0]), size=3.0,
                           name="Soft Floor", color=[0.3, 0.7, 0.4, 1.0])
        floor_def = DeformableBody.from_rigid_body(floor, mass=2.0,
                                                   stiffness=300, damping=10,
                                                   solver='msd')
        bodies.append(floor_def)

        # Rigid objects falling
        for i in range(3):
            obj = create_sphere(center=np.array([i * 0.8 - 0.8, 2.0 + i * 0.5, 0.0]),
                                radius=0.3, rings=6, sectors=8,
                                name=f"Rigid_{i}", color=[0.8, 0.6, 0.2, 1.0])
            bodies.append(obj)

    elif demo_name == 'rigid_collisions':
        # Rigid objects approaching each other
        for i in range(4):
            x = (i - 1.5) * 1.2
            obj = create_box(center=np.array([x, 0.0, 0.0]), size=0.6,
                             name=f"Cube_{i}",
                             color=[0.2 + i * 0.2, 0.5, 0.8 - i * 0.15, 1.0])
            bodies.append(obj)

    elif demo_name == 'deformable_collisions':
        # Deformable objects
        for i in range(3):
            sph = create_sphere(center=np.array([i * 1.0 - 1.0, 0.0, 0.0]),
                                radius=0.4, rings=8, sectors=10,
                                name=f"Soft_{i}",
                                color=[0.7, 0.3 + i * 0.2, 0.5, 1.0])
            soft = DeformableBody.from_rigid_body(sph, mass=0.5,
                                                  stiffness=200, damping=3,
                                                  solver='xpbd')
            bodies.append(soft)

    elif demo_name == 'mixed':
        # Rigid floor
        floor = create_box(center=np.array([0.0, -2.0, 0.0]), size=4.0,
                           name="Floor", color=[0.5, 0.5, 0.5, 1.0])
        bodies.append(floor)
        # Deformable blob
        blob = create_sphere(center=np.array([0.0, 0.0, 0.0]), radius=0.6,
                             rings=8, sectors=10, name="Blob",
                             color=[0.2, 0.8, 0.3, 1.0])
        soft_blob = DeformableBody.from_rigid_body(blob, mass=1.0,
                                                   stiffness=150, damping=5,
                                                   solver='msd')
        bodies.append(soft_blob)
        # Rigid projectiles
        for i in range(3):
            proj = create_box(center=np.array([i * 0.7 - 0.7, 2.0 + i * 0.4, 0.5]),
                              size=0.3, name=f"Proj_{i}",
                              color=[0.9, 0.2, 0.1, 1.0])
            bodies.append(proj)

    return bodies
