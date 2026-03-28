"""
FastAPI route definitions for the UDEC Haptic SIM application.

Provides REST endpoints for scene management and a WebSocket
endpoint for real-time simulation streaming.

Endpoints
---------
GET  /api/health          Health check
GET  /api/scene           Current scene state
POST /api/step            Simulation step
POST /api/scene/reset     Reset to default scene
POST /api/scene/load      Load OBJ file
POST /api/scene/random    Generate random scene
GET  /api/models          List available models
POST /api/scene/load-builtin  Load a built-in model
POST /api/probe           Update probe position
POST /api/settings        Update simulation parameters
POST /api/transform       Transform a body
POST /api/make-deformable Convert body to deformable
WS   /ws                  Real-time simulation WebSocket
"""
import json
import asyncio
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List

from ..simulation.scene import Scene
from ..simulation.obj_loader import load_obj, load_builtin, list_builtin_models, create_torus
from ..simulation.scene_generator import generate_random_scene
from ..simulation.deformable import DeformableBody

import numpy as np
import tempfile
import os

router = APIRouter()

# Global scene instance
scene = Scene()
scene.load_default_scene()


# ======================================================================
# Pydantic models
# ======================================================================

class ProbeUpdate(BaseModel):
    """Probe position update from the frontend."""
    x: float
    y: float
    z: float


class SettingsUpdate(BaseModel):
    """Simulation parameter update."""
    stiffness: Optional[float] = None
    damping: Optional[float] = None
    max_force: Optional[float] = None
    contact_threshold: Optional[float] = None
    show_octree: Optional[bool] = None
    octree_max_depth: Optional[int] = None
    spatial_method: Optional[str] = None
    probe_mode: Optional[str] = None
    spatial_max_depth: Optional[int] = None
    deformable_stiffness: Optional[float] = None
    deformable_damping: Optional[float] = None
    deformable_mass: Optional[float] = None
    deformable_solver: Optional[str] = None
    xpbd_iterations: Optional[int] = None
    show_spatial_viz: Optional[bool] = None
    push_radius: Optional[float] = None
    push_strength: Optional[float] = None


class TransformRequest(BaseModel):
    """Transformation request for a body."""
    body_index: int
    transform_type: str  # "translate", "rotate", "scale"
    dx: Optional[float] = 0.0
    dy: Optional[float] = 0.0
    dz: Optional[float] = 0.0
    angle: Optional[float] = 0.0
    axis_x: Optional[float] = 0.0
    axis_y: Optional[float] = 1.0
    axis_z: Optional[float] = 0.0
    factor: Optional[float] = 1.0


class MakeDeformableRequest(BaseModel):
    """Request to convert a body to deformable."""
    body_index: int
    mass: Optional[float] = 1.0
    stiffness: Optional[float] = 500.0
    damping: Optional[float] = 5.0
    solver: Optional[str] = "msd"


class LoadBuiltinRequest(BaseModel):
    """Request to load a built-in model."""
    model_name: str
    color: Optional[List[float]] = None


class CutRequest(BaseModel):
    """Request to cut a deformable body with a plane."""
    body_index: int
    point: List[float]  # [x, y, z] point on the cutting plane
    normal: List[float]  # [nx, ny, nz] plane normal


class RandomSceneRequest(BaseModel):
    """Request to generate a random scene."""
    num_bodies: Optional[int] = 5
    deformable_fraction: Optional[float] = 0.3


# ======================================================================
# REST endpoints
# ======================================================================

@router.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "bodies": len(scene.bodies)}


@router.get("/api/scene")
async def get_scene():
    """Return cached scene state without recomputing."""
    return scene.get_state()


@router.post("/api/step")
async def step_scene():
    """Run one simulation step and return state."""
    return scene.step()


@router.post("/api/scene/reset")
async def reset_scene():
    """Reset the scene to the default demo configuration."""
    scene.load_default_scene()
    scene.step()
    return {"status": "reset", "bodies": len(scene.bodies)}


@router.post("/api/scene/load")
async def load_model(file: UploadFile = File(...)):
    """Upload and load a Wavefront OBJ file into the scene."""
    if not file.filename.lower().endswith(".obj"):
        return {"error": "Only .obj files are supported"}

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
        body = load_obj(tmp_path)
        scene.add_body(body)
        return {"status": "loaded", "name": body.name, "bodies": len(scene.bodies)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)


@router.post("/api/scene/random")
async def random_scene(req: RandomSceneRequest = RandomSceneRequest()):
    """Generate a random scene with mixed body types."""
    scene.clear()
    bodies = generate_random_scene(
        num_bodies=req.num_bodies,
        deformable_fraction=req.deformable_fraction,
    )
    for body in bodies:
        scene.add_body(body)
    scene.step()
    return {"status": "random", "bodies": len(scene.bodies)}


@router.get("/api/models")
async def get_models():
    """List available built-in model names."""
    builtins = list_builtin_models()
    primitives = ["box", "sphere", "torus"]
    return {"primitives": primitives, "builtins": builtins}


@router.post("/api/scene/load-builtin")
async def load_builtin_model(req: LoadBuiltinRequest):
    """Load a built-in model into the scene."""
    try:
        if req.model_name == "torus":
            body = create_torus(
                center=np.array([0.0, 0.5, 0.0]),
                name="torus",
                color=req.color,
            )
        elif req.model_name in ("box", "sphere"):
            from ..simulation.obj_loader import create_box, create_sphere
            if req.model_name == "box":
                body = create_box(
                    center=np.array([0.0, 0.5, 0.0]),
                    name="box",
                    color=req.color,
                )
            else:
                body = create_sphere(
                    center=np.array([0.0, 0.5, 0.0]),
                    name="sphere",
                    color=req.color,
                )
        else:
            body = load_builtin(req.model_name, color=req.color)
        scene.add_body(body)
        return {"status": "loaded", "name": body.name, "bodies": len(scene.bodies)}
    except Exception as e:
        return {"error": str(e)}


class DemoSceneRequest(BaseModel):
    """Request to load a demo scene."""
    name: str = "falling_objects"


@router.post("/api/scene/demo")
async def load_demo(req: DemoSceneRequest = DemoSceneRequest()):
    """Load a preset demo scene."""
    scene.load_demo_scene(req.name)
    return scene.step()


class AnchorUpdate(BaseModel):
    """Surface contact point reported by the frontend raycaster."""
    x: float
    y: float
    z: float
    contacting: bool = True


@router.post("/api/probe")
async def update_probe(update: ProbeUpdate):
    """Update the probe position, recompute force, return full state."""
    scene.set_probe_position(np.array([update.x, update.y, update.z]))
    return scene.step()


@router.post("/api/anchor")
async def update_anchor(update: AnchorUpdate):
    """Set the force anchor point (from frontend raycasting)."""
    if update.contacting:
        scene.force_model.set_anchor(np.array([update.x, update.y, update.z]))
    else:
        scene.force_model.release()
    return scene.step()


@router.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update simulation parameters."""
    if settings.stiffness is not None:
        scene.force_model.stiffness = settings.stiffness
    if settings.damping is not None:
        scene.force_model.damping = settings.damping
    if settings.max_force is not None:
        scene.force_model.max_force = settings.max_force
    if settings.contact_threshold is not None:
        scene.contact_threshold = settings.contact_threshold
    if settings.show_octree is not None:
        scene.show_octree = settings.show_octree
    if settings.octree_max_depth is not None:
        scene.octree_max_depth = settings.octree_max_depth
    if settings.spatial_method is not None:
        scene.set_spatial_method(settings.spatial_method)
    if settings.probe_mode is not None:
        scene.probe_controller.set_mode(settings.probe_mode, scene)
    if settings.spatial_max_depth is not None:
        scene.spatial_max_depth = settings.spatial_max_depth
    if settings.show_spatial_viz is not None:
        scene.show_spatial_viz = settings.show_spatial_viz
    if settings.push_radius is not None:
        scene.probe_controller.push_radius = settings.push_radius
    if settings.push_strength is not None:
        scene.probe_controller.push_strength = settings.push_strength

    # Apply deformable settings to all deformable bodies
    for body in scene.bodies:
        if isinstance(body, DeformableBody):
            if settings.deformable_stiffness is not None:
                body.stiffness = settings.deformable_stiffness
            if settings.deformable_damping is not None:
                body.damping = settings.deformable_damping
            if settings.deformable_mass is not None:
                body.masses[:] = settings.deformable_mass
            if settings.deformable_solver is not None:
                body.solver = settings.deformable_solver
            if settings.xpbd_iterations is not None:
                body.xpbd_iterations = settings.xpbd_iterations

    return {"status": "updated"}


@router.post("/api/transform")
async def transform_body(req: TransformRequest):
    """Apply a transformation to a body."""
    if req.body_index < 0 or req.body_index >= len(scene.bodies):
        return {"error": "Invalid body index"}

    body = scene.bodies[req.body_index]

    if req.transform_type == "translate":
        body.translate(np.array([req.dx, req.dy, req.dz]))
    elif req.transform_type == "rotate":
        body.rotate(
            np.array([req.axis_x, req.axis_y, req.axis_z]),
            req.angle,
        )
    elif req.transform_type == "scale":
        body.scale(req.factor)
    else:
        return {"error": f"Unknown transform: {req.transform_type}"}

    scene.mark_bodies_dirty()
    return scene.step()


@router.post("/api/make-deformable")
async def make_deformable(req: MakeDeformableRequest):
    """Convert a rigid body to deformable."""
    success = scene.make_body_deformable(
        req.body_index,
        mass=req.mass,
        stiffness=req.stiffness,
        damping=req.damping,
        solver=req.solver,
    )
    if success:
        return scene.step()
    return {"error": "Could not convert body (invalid index or already deformable)"}


@router.post("/api/cut")
async def cut_body(req: CutRequest):
    """Cut a deformable body along a plane.

    The body must be deformable. The cut plane is defined by a point
    and normal vector. Returns the updated scene state.
    """
    point = np.array(req.point, dtype=np.float64)
    normal = np.array(req.normal, dtype=np.float64)
    n_created = scene.cut_body(req.body_index, point, normal)
    if n_created < 0:
        return {"error": "Invalid body index or body is not deformable"}
    state = scene.step()
    state["cut_result"] = {"new_vertices": n_created}
    return state


# ======================================================================
# WebSocket for real-time simulation
# ======================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time simulation WebSocket.

    The client sends JSON messages with probe position updates.
    The server responds with the full scene state including
    collision data and force vectors.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type", "step")

            if msg_type == "probe":
                scene.set_probe_position(
                    np.array([msg.get("x", 0), msg.get("y", 0), msg.get("z", 0)])
                )

            elif msg_type == "settings":
                if "stiffness" in msg:
                    scene.force_model.stiffness = msg["stiffness"]
                if "damping" in msg:
                    scene.force_model.damping = msg["damping"]
                if "max_force" in msg:
                    scene.force_model.max_force = msg["max_force"]
                if "show_octree" in msg:
                    scene.show_octree = msg["show_octree"]
                if "spatial_method" in msg:
                    scene.set_spatial_method(msg["spatial_method"])
                if "probe_mode" in msg:
                    scene.probe_controller.set_mode(msg["probe_mode"], scene)
                if "show_spatial_viz" in msg:
                    scene.show_spatial_viz = msg["show_spatial_viz"]

            elif msg_type == "transform":
                idx = msg.get("body_index", 0)
                if 0 <= idx < len(scene.bodies):
                    body = scene.bodies[idx]
                    t = msg.get("transform_type", "translate")
                    if t == "translate":
                        body.translate(np.array([
                            msg.get("dx", 0), msg.get("dy", 0), msg.get("dz", 0)
                        ]))
                    elif t == "rotate":
                        body.rotate(
                            np.array([
                                msg.get("axis_x", 0),
                                msg.get("axis_y", 1),
                                msg.get("axis_z", 0),
                            ]),
                            msg.get("angle", 0),
                        )

            elif msg_type == "reset":
                scene.load_default_scene()

            elif msg_type == "random":
                scene.clear()
                bodies = generate_random_scene(
                    num_bodies=msg.get("num_bodies", 5),
                    deformable_fraction=msg.get("deformable_fraction", 0.3),
                )
                for body in bodies:
                    scene.add_body(body)

            # Step and send state
            state = scene.step()
            await websocket.send_text(json.dumps(state))

    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
