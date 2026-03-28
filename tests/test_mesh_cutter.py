"""
Tests for mesh cutting operations.

Tests plane classification, no-cut same-side, triangle splitting,
and full deformable body cutting.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.mesh_cutter import cut_mesh_with_plane, cut_deformable_body
from app.simulation.deformable import DeformableBody
from app.simulation.obj_loader import create_box


def test_plane_classification():
    """Vertices should be correctly classified as above/below a plane."""
    # Simple triangle: one vertex above, two below the y=0 plane
    vertices = np.array([
        [0.0, 1.0, 0.0],   # above
        [-1.0, -1.0, 0.0],  # below
        [1.0, -1.0, 0.0],   # below
    ])
    faces = np.array([[0, 1, 2]])

    plane_point = np.array([0.0, 0.0, 0.0])
    plane_normal = np.array([0.0, 1.0, 0.0])

    new_verts, new_faces = cut_mesh_with_plane(vertices, faces, plane_point, plane_normal)

    # Should have created 2 new vertices (intersections on edges 0-1 and 0-2)
    assert len(new_verts) == 5, f"Expected 5 vertices, got {len(new_verts)}"
    # Should have split into 3 triangles
    assert len(new_faces) == 3, f"Expected 3 faces, got {len(new_faces)}"

    # New vertices should be on the plane (y ~ 0)
    for v in new_verts[3:]:
        assert abs(v[1]) < 1e-6, f"Intersection vertex should be on plane, y={v[1]}"

    print("  [PASS] Plane classification")


def test_no_cut_same_side():
    """When all vertices are on the same side, mesh should be unchanged."""
    vertices = np.array([
        [0.0, 1.0, 0.0],
        [1.0, 2.0, 0.0],
        [0.5, 1.5, 1.0],
    ])
    faces = np.array([[0, 1, 2]])

    # Plane at y=-5 -- all vertices are above
    plane_point = np.array([0.0, -5.0, 0.0])
    plane_normal = np.array([0.0, 1.0, 0.0])

    new_verts, new_faces = cut_mesh_with_plane(vertices, faces, plane_point, plane_normal)

    assert len(new_verts) == 3, f"Expected 3 vertices (unchanged), got {len(new_verts)}"
    assert len(new_faces) == 1, f"Expected 1 face (unchanged), got {len(new_faces)}"
    np.testing.assert_array_equal(new_faces[0], [0, 1, 2])
    print("  [PASS] No cut same side")


def test_cut_splits_triangle():
    """A plane cutting through a single triangle should split it into 3."""
    # Equilateral-ish triangle straddling y=0
    vertices = np.array([
        [0.0, 2.0, 0.0],   # above
        [-1.0, -1.0, 0.0],  # below
        [1.0, -1.0, 0.0],   # below
    ])
    faces = np.array([[0, 1, 2]])

    plane_point = np.array([0.0, 0.0, 0.0])
    plane_normal = np.array([0.0, 1.0, 0.0])

    new_verts, new_faces = cut_mesh_with_plane(vertices, faces, plane_point, plane_normal)

    # 1 above, 2 below -> 3 new faces, 2 new vertices
    assert len(new_verts) == 5, f"Expected 5 total vertices, got {len(new_verts)}"
    assert len(new_faces) == 3, f"Expected 3 faces after split, got {len(new_faces)}"

    # All face indices should be valid
    for face in new_faces:
        for idx in face:
            assert 0 <= idx < len(new_verts), f"Invalid face index {idx}"

    print("  [PASS] Cut splits triangle")


def test_deformable_body_cut():
    """Cutting a deformable body should update vertices, faces, and springs."""
    box = create_box(np.array([0, 0, 0.0]), size=2.0)
    deformable = DeformableBody.from_rigid_body(box)

    old_n_verts = len(deformable.vertices)
    old_n_faces = len(deformable.faces)
    old_n_springs = len(deformable.springs)

    # Cut through the center with a horizontal plane
    n_created = cut_deformable_body(
        deformable,
        plane_point=np.array([0.0, 0.0, 0.0]),
        plane_normal=np.array([0.0, 1.0, 0.0]),
    )

    assert n_created > 0, "Cut should create new vertices"
    assert len(deformable.vertices) == old_n_verts + n_created
    assert len(deformable.faces) > old_n_faces, "Cut should increase face count"
    assert len(deformable.springs) > old_n_springs, "Cut should increase spring count"

    # Velocities and masses should be extended
    assert len(deformable.velocities) == len(deformable.vertices)
    assert len(deformable.masses) == len(deformable.vertices)

    # Normals and AABB should be valid
    assert deformable.normals is not None
    assert len(deformable.normals) == len(deformable.faces)

    print(f"  [PASS] Deformable body cut ({n_created} new verts, "
          f"{len(deformable.faces)} faces, {len(deformable.springs)} springs)")


def test_cut_no_effect_when_plane_outside():
    """Cutting outside the mesh should not change it."""
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    deformable = DeformableBody.from_rigid_body(box)

    old_n_verts = len(deformable.vertices)

    n_created = cut_deformable_body(
        deformable,
        plane_point=np.array([0.0, 100.0, 0.0]),
        plane_normal=np.array([0.0, 1.0, 0.0]),
    )

    assert n_created == 0, "No cut should happen when plane is outside"
    assert len(deformable.vertices) == old_n_verts
    print("  [PASS] No effect when plane outside mesh")


def test_scene_cut_body():
    """Scene.cut_body should work for valid deformable body."""
    from app.simulation.scene import Scene
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=2.0)
    deformable = DeformableBody.from_rigid_body(box)
    scene.add_body(deformable)

    n = scene.cut_body(0, np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
    assert n > 0, "Scene.cut_body should create new vertices"
    print(f"  [PASS] Scene.cut_body ({n} new verts)")


def test_scene_cut_body_invalid():
    """Scene.cut_body should return -1 for invalid index or rigid body."""
    from app.simulation.scene import Scene
    scene = Scene()
    box = create_box(np.array([0, 0, 0.0]), size=1.0)
    scene.add_body(box)

    assert scene.cut_body(-1, np.zeros(3), np.array([0, 1, 0.0])) == -1
    assert scene.cut_body(99, np.zeros(3), np.array([0, 1, 0.0])) == -1
    # Rigid body can't be cut
    assert scene.cut_body(0, np.zeros(3), np.array([0, 1, 0.0])) == -1
    print("  [PASS] Scene.cut_body invalid cases")


if __name__ == "__main__":
    print("=== Mesh Cutter Tests ===")
    test_plane_classification()
    test_no_cut_same_side()
    test_cut_splits_triangle()
    test_deformable_body_cut()
    test_cut_no_effect_when_plane_outside()
    test_scene_cut_body()
    test_scene_cut_body_invalid()
    print("=== All mesh cutter tests passed ===")
