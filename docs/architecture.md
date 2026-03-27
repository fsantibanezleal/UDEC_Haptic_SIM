# System Architecture

## Overview

The UDEC Haptic SIM is a client-server application consisting of:

- **Backend**: Python/FastAPI server running the simulation engine (scene management, collision detection, force computation)
- **Frontend**: HTML5/Three.js browser application providing 3D visualization and user interaction
- **Communication**: WebSocket for real-time bidirectional state streaming, REST endpoints for configuration

## Architecture Diagram

![System Architecture](svg/architecture.svg)

## Backend Components

| Module | File | Responsibility |
|--------|------|---------------|
| Scene Manager | `scene.py` | Orchestrates bodies, probe, octree, and physics each frame |
| Rigid Body | `rigid_body.py` | Mesh storage, normals, AABB, transformations |
| Octree Engine | `collision.py` | Spatial partitioning and SAT-based collision detection |
| Physics Engine | `physics.py` | Spring-damper force model and surface proximity queries |
| OBJ Loader | `obj_loader.py` | Wavefront OBJ parser and primitive mesh generators |
| Transforms | `transform.py` | Rodrigues rotation, rotation matrices, quaternions |
| API Routes | `routes.py` | REST endpoints and WebSocket handler |

## Frontend Components

| Module | File | Responsibility |
|--------|------|---------------|
| 3D Renderer | `renderer3d.js` | Three.js scene, mesh rendering, octree wireframes |
| Controls | `controls.js` | Slider/button bindings, parameter synchronization |
| WebSocket | `websocket.js` | Connection management, auto-reconnect |
| App | `app.js` | Initialization, render loop, periodic step requests |

## Data Flow

1. **User moves probe** (slider input) -> `controls.js` sends `{type: "probe", x, y, z}` via WebSocket
2. **Server receives** -> updates `scene.probe_position`, calls `scene.step()`
3. **Simulation step**:
   - Rebuild octree over all bodies
   - Run collision detection (broad phase + SAT narrow phase)
   - Find nearest surface to probe
   - Compute spring-damper feedback force
4. **Server sends** full scene state JSON back via WebSocket
5. **Frontend receives** -> `renderer3d.js` updates Three.js meshes, force arrow, overlays

## Port Configuration

The application runs on **port 8006** by default:

```bash
uvicorn app.main:app --port 8006
```
