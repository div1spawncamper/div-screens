"""FastAPI server for the editor UI and live preview."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

logger = logging.getLogger("div-screens.api")

app = FastAPI(title="div-screens", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# These will be set by main.py at startup
screen_manager = None
render_engine = None
layouts_dir = None


@app.get("/api/screens")
async def get_screens():
    """List all connected screens."""
    if screen_manager:
        return screen_manager.list_screens()
    return []


@app.get("/api/screens/scan")
async def scan_screens():
    """Scan for available screens (without connecting)."""
    from ..screens.protocol import TuringScreen
    return TuringScreen.auto_detect()


@app.get("/api/layouts")
async def list_layouts():
    """List all available layouts."""
    if not layouts_dir:
        return []
    results = []
    for f in Path(layouts_dir).glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
            results.append({
                "file": f.name,
                "name": data.get("name", f.stem),
                "screen": data.get("screen", {}),
            })
        except:
            pass
    return results


@app.get("/api/layouts/{name}")
async def get_layout(name: str):
    """Get a specific layout by filename."""
    path = Path(layouts_dir) / name
    if not path.exists():
        return JSONResponse({"error": "not found"}, 404)
    with open(path) as f:
        return json.load(f)


@app.post("/api/layouts/{name}")
async def save_layout(name: str, layout: dict):
    """Save a layout."""
    path = Path(layouts_dir) / name
    with open(path, "w") as f:
        json.dump(layout, f, indent=2)
    return {"status": "saved", "file": name}


@app.get("/api/system/sources")
async def list_sources():
    """List all available data sources for widgets."""
    return {
        "cpu": ["percent", "percent_per_core", "frequency", "cores", "cores_physical"],
        "ram": ["percent", "used", "total"],
        "disk": {"metrics": ["percent", "used", "total", "label"], "note": "Use disk.<letter>.<metric>"},
        "net": ["upload_speed", "download_speed", "upload_speed_fmt", "download_speed_fmt", "total_sent", "total_recv"],
        "sys": ["uptime", "processes", "load"],
    }


@app.get("/api/widgets/types")
async def list_widget_types():
    """List available widget types and their config schemas."""
    return {
        "clock": {"config": ["format", "locale", "font", "fontSize", "color", "background", "align"]},
        "text": {"config": ["text", "source", "font", "fontSize", "color", "background", "align"]},
        "bar": {"config": ["source", "colorLow", "colorMid", "colorHigh", "thresholds", "radius", "barBackground"]},
        "mini_bars": {"config": ["source", "columns", "gap", "barHeight", "colorLow", "colorMid", "colorHigh"]},
        "separator": {"config": ["color"]},
        "image": {"config": ["path"]},
    }


# WebSocket for live preview
active_ws: list[WebSocket] = []


@app.websocket("/ws/preview")
async def preview_ws(websocket: WebSocket):
    """WebSocket endpoint for live frame preview."""
    await websocket.accept()
    active_ws.append(websocket)
    logger.info("Editor preview WebSocket connected")
    try:
        while True:
            # Keep alive, receive any editor commands
            data = await websocket.receive_text()
            # Could handle layout updates here
    except WebSocketDisconnect:
        active_ws.remove(websocket)
        logger.info("Editor preview WebSocket disconnected")
