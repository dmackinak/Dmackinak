import os
import json
import uuid
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from processing.pipeline import process_video

# ── Directories ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

for d in (UPLOAD_DIR, CLIPS_DIR):
    os.makedirs(d, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="YouTube Shorts Auto-Cutter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=2)

# In-memory job store (persists for the server lifetime)
jobs: dict = {}

# ── Settings ───────────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "channel_name": "",
    "watermark_position": "bottom-right",
    "watermark_color": "#FFFFFF",
    "watermark_size": 28,
    "short_duration_min": 20,
    "short_duration_max": 55,
    "max_clips": 5,
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(data: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


class SettingsModel(BaseModel):
    channel_name: str = ""
    watermark_position: str = "bottom-right"
    watermark_color: str = "#FFFFFF"
    watermark_size: int = 28
    short_duration_min: int = 20
    short_duration_max: int = 55
    max_clips: int = 5


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.put("/api/settings")
def update_settings(s: SettingsModel):
    data = s.model_dump()
    save_settings(data)
    return data


# ── Upload ─────────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")

    content = await file.read()
    with open(video_path, "wb") as f:
        f.write(content)

    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "message": "Queued...",
        "filename": file.filename,
        "created_at": datetime.now().isoformat(),
        "clips": [],
        "error": None,
    }

    settings = load_settings()
    background_tasks.add_task(_run_job, job_id, video_path, settings)
    return {"job_id": job_id}


async def _run_job(job_id: str, video_path: str, settings: dict):
    jobs[job_id]["status"] = "processing"

    def _progress(pct: int, msg: str):
        jobs[job_id]["progress"] = pct
        jobs[job_id]["message"] = msg

    clips_dir = os.path.join(CLIPS_DIR, job_id)
    os.makedirs(clips_dir, exist_ok=True)

    loop = asyncio.get_event_loop()
    try:
        clips = await loop.run_in_executor(
            executor,
            process_video,
            video_path,
            clips_dir,
            settings,
            _progress,
        )
        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "message": f"Done! Generated {len(clips)} Short(s).",
            "clips": clips,
        })
    except Exception as exc:
        jobs[job_id].update({
            "status": "error",
            "progress": 0,
            "message": f"Error: {exc}",
            "error": str(exc),
        })
    finally:
        # Clean up original upload to save space
        if os.path.exists(video_path):
            os.remove(video_path)


# ── Job status ─────────────────────────────────────────────────────────────────
@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


@app.get("/api/jobs")
def list_jobs():
    return list(jobs.values())


# ── Clip download ──────────────────────────────────────────────────────────────
@app.get("/api/clips/{job_id}/{clip_name}")
def get_clip(job_id: str, clip_name: str):
    # Security: prevent path traversal
    safe_name = os.path.basename(clip_name)
    clip_path = os.path.join(CLIPS_DIR, job_id, safe_name)
    if not os.path.exists(clip_path):
        raise HTTPException(404, "Clip not found")
    return FileResponse(clip_path, media_type="video/mp4", filename=safe_name)


# ── Serve built frontend (SPA-aware) ──────────────────────────────────────────
FRONTEND_DIST = os.path.join(BASE_DIR, "..", "frontend", "dist")
_ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")

if os.path.exists(_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all non-API routes so React Router works."""
    index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    raise HTTPException(404, "Frontend not built. Run: cd frontend && npm run build")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
