# Development History

## v2.0.0 (2026-03-26) -- Modern Python/Web Reimplementation

### Motivation

- The original PHANToM Omni hardware is no longer in production (3D Systems discontinued OpenHaptics support)
- C++/CLI and Windows Forms are deprecated technologies
- OpenGL immediate mode is obsolete (replaced by WebGL/Vulkan)
- Modern web technologies provide cross-platform accessibility

### Technical Stack

- **Backend**: Python 3.12, FastAPI, uvicorn (ASGI)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Three.js r128
- **Communication**: WebSocket (bidirectional real-time)
- **Simulation**: NumPy for vectorized math
- **Port**: 8006

### Physics Engine

#### Spring-Damper Force Model
The haptic force feedback is modeled as a spring-damper system:
```
F = -k·x - b·v
```
where:
- k = spring stiffness constant
- x = penetration depth vector
- b = damping coefficient
- v = relative velocity

This replaces the PHANToM Omni hardware force rendering with a software-based model driven by mouse/slider input.

#### Separating Axis Theorem (SAT) Collision Detection
Triangle-triangle intersection is tested using the full SAT with 11 potential separating axes:

```
SAT 11 axes test:
  - 2 triangle normals (n_A, n_B)
  - 9 edge cross products (e_Ai x e_Bj, i=0..2, j=0..2)
```

For each axis, project both triangles and check for interval overlap. If any axis separates the triangles, there is no collision. This is geometrically exact, replacing the original vertex-proximity heuristic.

#### Octree Spatial Partitioning
Hierarchical spatial subdivision for O(log N) collision queries:

```
Child index: idx = (x >= cx) + 2·(y >= cy) + 4·(z >= cz)
```

where (cx, cy, cz) is the octant center. This maps each point to one of 8 children using bit arithmetic. Subdivision criteria preserved from original:
- `factorU = 4`: Minimum triangles to subdivide
- `factorG = 0.02`: Minimum occupancy ratio (2%)
- `factorR = 0.01`: Minimum spatial ratio (1%)

#### Rodrigues' Rotation Formula
Used for rotating force vectors and object orientations:
```
v_rot = v·cos(θ) + (k x v)·sin(θ) + k·(k·v)·(1-cos(θ))
```
where k is the unit rotation axis and θ is the rotation angle. This provides axis-angle rotation without constructing a full rotation matrix.

> See `docs/diagrams/architecture.svg` for visual reference.

### Architecture Mapping

| Original C++ | Modern Python | Notes |
|---------------|---------------|-------|
| `Cuerpo` struct | `RigidBody` class | NumPy arrays instead of raw floats |
| `Octrees` class | `Octree` class | Same subdivision criteria |
| `InteraccionTT` | `triangles_intersect()` | Upgraded from proximity to SAT |
| `Haptico` class | `SpringForceModel` class | Mouse/slider instead of PHANToM |
| `Cargador` loader | `load_obj()` function | Added fan triangulation |
| `DibujarOpenGl` | `renderer3d.js` | OpenGL -> Three.js/WebGL |
| `BigBangT` main | `Scene` + `main.py` | FastAPI + WebSocket |
| Windows Forms | HTML/CSS/JS | Dark theme, responsive layout |

### Key Improvements

1. **SAT collision detection**: The original used vertex proximity; the modern version uses proper Separating Axis Theorem for geometric correctness.
2. **Cross-platform**: Runs in any modern web browser -- no Windows, OpenGL, or hardware dependencies.
3. **Real-time visualization**: Three.js provides hardware-accelerated WebGL rendering with orbit controls, wireframe overlays, and force vector visualization.
4. **Modular architecture**: Clean separation of simulation engine, API layer, and frontend with documented interfaces.
5. **Comprehensive documentation**: Theory, architecture diagrams, and SVG visualizations.

---

## v1.x (~2008) -- Original C++/CLI + PHANToM Project [Legacy]

### Context

The original **UDEC Haptic SIM** project was developed at the **Universidad de Concepcion (UdeC)**, Chile, circa 2008. It was a research prototype for exploring haptic interaction with 3D virtual environments.

### Technology Stack

- **Language**: C++/CLI (managed C++ for .NET integration)
- **Graphics**: OpenGL (immediate mode rendering)
- **Haptic SDK**: OpenHaptics (SensAble Technologies)
- **Haptic Device**: PHANToM Omni (3-DOF force feedback)
- **Platform**: Windows XP/Vista, Visual Studio 2005
- **UI Framework**: Windows Forms (managed C++ wrappers)

### Project Structure

The original project was named **NitrogenoAdvanced** with the solution **BigBangT**:

| File | Purpose |
|------|---------|
| `BigBangT.cpp` | Application entry point and main loop |
| `Cuerpo.cpp/h` | Rigid body ("Cuerpo" = body in Spanish) -- mesh, normals, AABB |
| `Octrees.cpp/h` | Octree spatial partitioning with factorU, factorG, factorR |
| `InteraccionTT.cpp/h` | Triangle-triangle interaction testing |
| `Haptico.cpp/h` | Single PHANToM device haptic rendering |
| `HapticoDoble.cpp/h` | Dual PHANToM device support |
| `Cargador.cpp/h` | Wavefront OBJ file loader |
| `DibujarOpenGl.cpp/h` | OpenGL rendering functions |
| `OpenForPanel.cpp/h` | OpenGL panel management |
| `OpenHija.cpp/h` | Child OpenGL window |
| `VentanaPadre.cpp/h` | Main parent window (Windows Forms) |
| `VentanaHija.cpp/h` | Child window with OpenGL viewport |
| `VentanaOctree.cpp/h` | Octree visualization window |
| `GeoBasica.h` | Basic geometric types and operations |
| `ColorGl.h` | OpenGL color definitions |

### Key Design Decisions

1. **Octree parameters** were tuned for the PHANToM's 1 kHz haptic loop:
   - `factorU = 4`: Minimum triangles to subdivide
   - `factorG = 0.02`: Minimum occupancy ratio (2%)
   - `factorR = 0.01`: Minimum spatial ratio (1%)

2. **Dual haptic support** allowed two PHANToM devices simultaneously for bimanual interaction experiments.

3. **Collision faces** were colour-coded in the OpenGL render: red faces indicated triangle-triangle penetration.

### Preserved Legacy Code

The original C++ source files are preserved in the `legacy/` directory for reference. They are not required to run the current version of the application.

---

## Timeline

| Date | Milestone |
|------|-----------|
| ~2008 | Original C++/CLI + OpenGL + PHANToM project at UdeC |
| 2024 | Legacy code archived in repository |
| 2026-03-26 | Modern Python/FastAPI/Three.js reimplementation |
