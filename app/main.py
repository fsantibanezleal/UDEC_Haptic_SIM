"""
UDEC Haptic SIM -- FastAPI application entry point.

A modern Python/Three.js web application that recreates the 2008
C++/CLI haptic simulation from the Universidad de Concepcion.
Instead of physical PHANToM haptic hardware, the probe is
controlled via mouse/keyboard interaction in the browser.

Run with::

    uvicorn app.main:app --port 8006 --reload

Then open http://localhost:8006 in a browser.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(
    title="UDEC Haptic SIM",
    description=(
        "Web-based 3D haptic simulation with octree collision detection, "
        "spring-based force feedback, and Three.js visualisation."
    ),
    version="1.0.0",
)

# CORS — allow all origins so fetch() works from any context
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (BEFORE static mount so /api/* takes priority)
app.include_router(router)

# Serve static files
static_dir = Path(__file__).parent / "static"


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse(str(static_dir / "index.html"))


# Mount static LAST so it doesn't shadow API routes
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
