from __future__ import annotations

import logging
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.runtime.context import RUNS_ROOT
from core.runtime.discovery import list_available_runs
from interface.cli.utils import run_named_job

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static-file directory: the Next.js export lives at frontend/out/
# ---------------------------------------------------------------------------
_STATIC_DIR = Path(__file__).parent / "frontend" / "out"

# ---------------------------------------------------------------------------
# In-memory job registry (process-local; reset on server restart)
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Custom log handler that routes records into a job's log list
# ---------------------------------------------------------------------------
class _JobLogHandler(logging.Handler):
    def __init__(self, job_id: str) -> None:
        super().__init__()
        self._job_id = job_id
        self.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            with _jobs_lock:
                entry = _jobs.get(self._job_id)
                if entry is not None:
                    entry["logs"].append(msg)
        except Exception:  # noqa: BLE001
            self.handleError(record)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Crucible Web Interface", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Allow the Next.js dev server (port 3000) during development.
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class SaveConfigBody(BaseModel):
    content: str


class LaunchBody(BaseModel):
    config: str = "default"
    overrides: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_config_path(run_name: str, config_name: str) -> Path:
    config_dir = RUNS_ROOT / run_name / "configs"
    for ext in (".yaml", ".yml"):
        path = config_dir / f"{config_name}{ext}"
        if path.exists():
            return path
    raise HTTPException(
        status_code=404,
        detail=f"Config '{config_name}' not found for run '{run_name}'.",
    )


def _make_job_record(
    job_id: str, run_name: str, config_name: str, overrides: list[str]
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "run_name": run_name,
        "config_name": config_name,
        "overrides": overrides,
        "status": "pending",
        "started_at": time.time(),
        "finished_at": None,
        "output": None,
        "logs": [],
    }


def _run_job_in_background(job_id: str, run_name: str, config_name: str, overrides: list[str]) -> None:
    handler = _JobLogHandler(job_id)
    root = logging.getLogger()
    root.addHandler(handler)

    with _jobs_lock:
        entry = _jobs.get(job_id)
        if entry is not None:
            entry["status"] = "running"

    try:
        result = run_named_job(
            run_name,
            config_name,
            overrides=overrides if overrides else None,
        )
        with _jobs_lock:
            entry = _jobs.get(job_id)
            if entry is not None:
                entry.update(
                    status="completed",
                    output=result,
                    finished_at=time.time(),
                )
    except Exception as exc:  # noqa: BLE001
        tb = traceback.format_exc()
        with _jobs_lock:
            entry = _jobs.get(job_id)
            if entry is not None:
                entry.update(
                    status="failed",
                    output=str(exc),
                    finished_at=time.time(),
                )
                entry["logs"].append(tb)
    finally:
        root.removeHandler(handler)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.get("/api/runs")
def get_runs() -> dict[str, list[str]]:
    """List all discovered run names."""
    return {"runs": list_available_runs()}


@app.get("/api/runs/{run_name}/config")
def get_config(run_name: str, config: str = "default") -> dict[str, str]:
    """Return the raw YAML content of a run's config file."""
    path = _find_config_path(run_name, config)
    return {"content": path.read_text(encoding="utf-8"), "path": str(path)}


@app.put("/api/runs/{run_name}/config")
def save_config(run_name: str, body: SaveConfigBody, config: str = "default") -> dict[str, str]:
    """Overwrite a run's YAML config file."""
    path = _find_config_path(run_name, config)
    path.write_text(body.content, encoding="utf-8")
    return {"status": "saved"}


@app.post("/api/runs/{run_name}/launch", status_code=202)
def launch_run(run_name: str, body: LaunchBody | None = None) -> dict[str, str]:
    """Launch a run asynchronously; returns the new job_id immediately."""
    if body is None:
        body = LaunchBody()

    # Validate that the run exists before queueing.
    if run_name not in list_available_runs():
        raise HTTPException(status_code=404, detail=f"Run '{run_name}' not found.")

    job_id = str(uuid.uuid4())
    record = _make_job_record(job_id, run_name, body.config, body.overrides)
    with _jobs_lock:
        _jobs[job_id] = record

    thread = threading.Thread(
        target=_run_job_in_background,
        args=(job_id, run_name, body.config, body.overrides),
        daemon=True,
        name=f"crucible-job-{job_id[:8]}",
    )
    thread.start()
    return {"job_id": job_id}


@app.get("/api/jobs")
def list_jobs() -> dict[str, list[dict[str, Any]]]:
    """Return all jobs, most-recent first."""
    with _jobs_lock:
        jobs = list(_jobs.values())
    return {"jobs": sorted(jobs, key=lambda j: j["started_at"], reverse=True)}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    """Return a single job record including captured log lines."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


# ---------------------------------------------------------------------------
# Serve the built Next.js static export (must come last)
# ---------------------------------------------------------------------------
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
else:

    @app.get("/")
    def ui_not_built_error() -> None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Frontend not built. "
                "Run `npm run build` inside interface/web/frontend/ first."
            ),
        )
