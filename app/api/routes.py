"""
FastAPI route definitions for the UDEC Haptic SIM application.

Provides REST endpoints for scene management and a WebSocket
endpoint for real-time simulation streaming.

Endpoints
---------
GET  /api/health        Health check
GET  /api/scene         Current scene state
POST /api/scene/reset   Reset to default scene
POST /api/scene/load    Load OBJ file
POST /api/probe         Update probe position
POST /api/settings      Update simulation parameters
WS   /ws                Real-time simulation WebSocket
"""
import json
import asyncio
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List

from ..simulation.scene import Scene
from ..simulation.obj_loader import load_obj

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


# ======================================================================
# REST endpoints
# ======================================================================

@router.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "bodies": len(scene.bodies)}


@router.get("/api/scene")
async def get_scene():
    """Return cached scene state without recomputing.

    Use POST /api/step to trigger a full recomputation.
    This endpoint is fast because it returns pre-computed data.
    """
    return scene.get_state()


@router.post("/api/step")
async def step_scene():
    """Run one simulation step (octree + collisions + force) and return state."""
    return scene.step()


@router.post("/api/scene/reset")
async def reset_scene():
    """Reset the scene to the default demo configuration."""
    scene.load_default_scene()
    scene.step()  # precompute
    return {"status": "reset", "bodies": len(scene.bodies)}


@router.post("/api/scene/load")
async def load_model(file: UploadFile = File(...)):
    """Upload and load a Wavefront OBJ file into the scene."""
    if not file.filename.lower().endswith(".obj"):
        return {"error": "Only .obj files are supported"}

    # Save to temp file, parse, then remove
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

    # Mark bodies as moved so octree+collisions get rebuilt
    scene.mark_bodies_dirty()
    return scene.step()


# ======================================================================
# WebSocket for real-time simulation
# ======================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time simulation WebSocket.

    The client sends JSON messages with probe position updates.
    The server responds with the full scene state including
    collision data and force vectors.

    Client message format::

        {"type": "probe", "x": 0.5, "y": 0.3, "z": 1.0}
        {"type": "settings", "stiffness": 0.3}
        {"type": "step"}

    Server response: full scene state dict.
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

            # Step and send state
            state = scene.step()
            await websocket.send_text(json.dumps(state))

    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
