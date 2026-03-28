"""
Tests for OBJ file parsing with texture coordinates and normals.
"""
import sys
import os
import tempfile
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.simulation.obj_loader import load_obj, parse_face_index, create_box


def _write_temp_obj(content: str) -> str:
    """Write OBJ content to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".obj")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def test_parse_face_index_vertex_only():
    """Parse 'v' format face token."""
    vi, ti, ni = parse_face_index("3")
    assert vi == 2  # 1-based to 0-based
    assert ti == -1
    assert ni == -1
    print("  [PASS] parse_face_index vertex only")


def test_parse_face_index_vertex_tex():
    """Parse 'v/vt' format face token."""
    vi, ti, ni = parse_face_index("3/5")
    assert vi == 2
    assert ti == 4
    assert ni == -1
    print("  [PASS] parse_face_index v/vt")


def test_parse_face_index_vertex_tex_normal():
    """Parse 'v/vt/vn' format face token."""
    vi, ti, ni = parse_face_index("3/5/7")
    assert vi == 2
    assert ti == 4
    assert ni == 6
    print("  [PASS] parse_face_index v/vt/vn")


def test_parse_face_index_vertex_skip_normal():
    """Parse 'v//vn' format face token."""
    vi, ti, ni = parse_face_index("3//7")
    assert vi == 2
    assert ti == -1
    assert ni == 6
    print("  [PASS] parse_face_index v//vn")


def test_load_obj_basic():
    """Load a basic OBJ without texture coordinates."""
    content = """\
# Simple triangle
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
f 1 2 3
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path, name="tri")
        assert body.name == "tri"
        assert body.vertices.shape == (3, 3)
        assert body.faces.shape == (1, 3)
        assert body.tex_coords is None
        assert body.has_texture is False
        print("  [PASS] load_obj basic (no textures)")
    finally:
        os.unlink(path)


def test_load_obj_with_texture_coords():
    """Load an OBJ with vt lines and f v/vt format."""
    content = """\
# Textured triangle
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 0.0 1.0
f 1/1 2/2 3/3
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path, name="textured_tri")
        assert body.vertices.shape == (3, 3)
        assert body.faces.shape == (1, 3)
        assert body.tex_coords is not None
        assert body.tex_coords.shape == (3, 2)
        assert body.has_texture is True
        np.testing.assert_allclose(body.tex_coords[0], [0.0, 0.0])
        np.testing.assert_allclose(body.tex_coords[1], [1.0, 0.0])
        np.testing.assert_allclose(body.tex_coords[2], [0.0, 1.0])
        print("  [PASS] load_obj with texture coordinates")
    finally:
        os.unlink(path)


def test_load_obj_with_normals():
    """Load an OBJ with vn lines and f v/vt/vn format."""
    content = """\
# Triangle with normals
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 0.0 1.0
vn 0.0 0.0 1.0
f 1/1/1 2/2/1 3/3/1
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path, name="normal_tri")
        assert body.has_texture is True
        assert body.tex_coords.shape == (3, 2)
        assert hasattr(body, 'file_normals')
        assert body.file_normals.shape == (1, 3)
        np.testing.assert_allclose(body.file_normals[0], [0.0, 0.0, 1.0])
        print("  [PASS] load_obj with normals")
    finally:
        os.unlink(path)


def test_load_obj_skip_normal_format():
    """Load an OBJ with f v//vn format (no texture)."""
    content = """\
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
vn 0.0 0.0 1.0
f 1//1 2//1 3//1
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path, name="skip_tex")
        assert body.tex_coords is None
        assert body.has_texture is False
        assert hasattr(body, 'file_normals')
        assert body.file_normals.shape == (1, 3)
        print("  [PASS] load_obj v//vn format")
    finally:
        os.unlink(path)


def test_load_obj_quad_triangulation_with_textures():
    """Quad faces should be fan-triangulated preserving texture indices."""
    content = """\
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
f 1/1 2/2 3/3 4/4
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path, name="quad")
        # Quad -> 2 triangles
        assert body.faces.shape == (2, 3)
        assert body.tex_coords is not None
        assert body.tex_coords.shape == (4, 2)
        assert body.has_texture is True
        print("  [PASS] load_obj quad triangulation with textures")
    finally:
        os.unlink(path)


def test_get_state_with_texture():
    """RigidBody.get_state() should include texture data when present."""
    content = """\
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 0.0 1.0
f 1/1 2/2 3/3
"""
    path = _write_temp_obj(content)
    try:
        body = load_obj(path)
        state = body.get_state()
        assert 'tex_coords' in state
        assert 'has_texture' in state
        assert state['has_texture'] is True
        assert len(state['tex_coords']) == 3
        print("  [PASS] get_state includes texture data")
    finally:
        os.unlink(path)


def test_get_state_without_texture():
    """RigidBody.get_state() should NOT include texture data by default."""
    box = create_box(np.array([0, 0, 0.0]))
    state = box.get_state()
    assert 'tex_coords' not in state
    assert 'has_texture' not in state
    print("  [PASS] get_state excludes texture data when absent")


if __name__ == "__main__":
    print("=== OBJ Loader Tests ===")
    test_parse_face_index_vertex_only()
    test_parse_face_index_vertex_tex()
    test_parse_face_index_vertex_tex_normal()
    test_parse_face_index_vertex_skip_normal()
    test_load_obj_basic()
    test_load_obj_with_texture_coords()
    test_load_obj_with_normals()
    test_load_obj_skip_normal_format()
    test_load_obj_quad_triangulation_with_textures()
    test_get_state_with_texture()
    test_get_state_without_texture()
    print("=== All OBJ loader tests passed ===")
