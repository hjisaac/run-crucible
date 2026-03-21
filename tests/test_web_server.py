"""Tests for the Crucible web API (interface/web/server.py).

Runs are discovered from a temporary directory injected via monkeypatching so
the tests are fully self-contained and do not depend on the real runs/ folder.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from textwrap import dedent

import pytest
from fastapi.testclient import TestClient

import core.runtime.context as runtime_context
import interface.cli.utils as ui_utils
import interface.web.server as web_server


def _clear_runs_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "runs" or module_name.startswith("runs."):
            del sys.modules[module_name]


_RUNNER_SOURCE = dedent(
    """
    from core.jobs import AbstractJob

    class Job(AbstractJob):
        def setup_data(self):
            pass

        def run(self):
            return {"status": "ok", "task": "demo_web_run"}

    JOB_CLASS = Job
    """
)


def _write_web_run_package(tmp_path: Path) -> Path:
    """Mirror the pattern used by test_interface_cli_pipeline.py."""
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "demo_web_run"
    configs_dir = run_dir / "configs"
    configs_dir.mkdir(parents=True)

    (runs_root / "__init__.py").write_text("", encoding="utf-8")
    (run_dir / "__init__.py").write_text(
        "from .runner import Job, JOB_CLASS\n__all__ = ['Job', 'JOB_CLASS']\n",
        encoding="utf-8",
    )
    (run_dir / "runner.py").write_text(_RUNNER_SOURCE, encoding="utf-8")

    log_dir = tmp_path / "runtime-logs"
    (configs_dir / "default.yaml").write_text(
        f"log_dir: {log_dir.as_posix()}\n"
        "log_console_level: WARNING\n"
        "log_file_level: DEBUG\n",
        encoding="utf-8",
    )
    return runs_root


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def demo_web_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runs_root = _write_web_run_package(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(runtime_context, "RUNS_ROOT", runs_root)
    monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
    monkeypatch.setattr(web_server, "RUNS_ROOT", runs_root)
    _clear_runs_modules()
    # Clear the in-memory job registry between tests
    with web_server._jobs_lock:
        web_server._jobs.clear()
    yield runs_root, "demo_web_run"
    # Wait briefly for any background threads to finish so Hydra global
    # state is not left dirty for the next test.
    deadline = time.time() + 3
    while time.time() < deadline:
        with web_server._jobs_lock:
            active = any(
                j["status"] in {"pending", "running"}
                for j in web_server._jobs.values()
            )
        if not active:
            break
        time.sleep(0.05)
    with web_server._jobs_lock:
        web_server._jobs.clear()
    _clear_runs_modules()


@pytest.fixture()
def client(demo_web_environment):
    return TestClient(web_server.app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# /api/runs
# ---------------------------------------------------------------------------

def test_get_runs_returns_list(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert run_name in data["runs"]


# ---------------------------------------------------------------------------
# /api/runs/{run_name}/config
# ---------------------------------------------------------------------------

def test_get_config_returns_yaml_content(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.get(f"/api/runs/{run_name}/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "log_dir" in data["content"]


def test_get_config_missing_run_returns_404(client, demo_web_environment):
    resp = client.get("/api/runs/nonexistent_run/config")
    assert resp.status_code == 404


def test_get_config_missing_config_name_returns_404(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.get(f"/api/runs/{run_name}/config?config=no_such_config")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/runs/{run_name}/config
# ---------------------------------------------------------------------------

def test_save_config_overwrites_yaml(client, demo_web_environment):
    runs_root, run_name = demo_web_environment
    new_content = "log_dir: logs\nlog_console_level: DEBUG\nlog_file_level: INFO\n"

    resp = client.put(
        f"/api/runs/{run_name}/config",
        json={"content": new_content},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"

    saved = (runs_root / run_name / "configs" / "default.yaml").read_text()
    assert saved == new_content


# ---------------------------------------------------------------------------
# POST /api/runs/{run_name}/launch
# ---------------------------------------------------------------------------

def test_launch_run_returns_job_id(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.post(f"/api/runs/{run_name}/launch", json={})
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID


def test_launch_unknown_run_returns_404(client, demo_web_environment):
    resp = client.post("/api/runs/nonexistent_run/launch", json={})
    assert resp.status_code == 404


def test_launch_creates_job_record(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.post(f"/api/runs/{run_name}/launch", json={})
    job_id = resp.json()["job_id"]

    job_resp = client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    job = job_resp.json()
    assert job["run_name"] == run_name
    assert job["status"] in {"pending", "running", "completed", "failed"}


def test_launch_job_completes(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.post(f"/api/runs/{run_name}/launch", json={})
    job_id = resp.json()["job_id"]

    # Poll until done (max 5 s)
    deadline = time.time() + 5
    job = None
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)

    assert job is not None
    assert job["status"] == "completed"
    assert job["output"] == {"status": "ok", "task": "demo_web_run"}


def test_launch_job_captures_logs(client, demo_web_environment):
    _, run_name = demo_web_environment
    resp = client.post(f"/api/runs/{run_name}/launch", json={})
    job_id = resp.json()["job_id"]

    deadline = time.time() + 5
    job = None
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)

    # logs is a list (may be empty if the job emits no log lines, but it should exist)
    assert isinstance(job["logs"], list)


# ---------------------------------------------------------------------------
# GET /api/jobs
# ---------------------------------------------------------------------------

def test_list_jobs_empty_initially(client, demo_web_environment):
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert resp.json()["jobs"] == []


def test_list_jobs_returns_launched_job(client, demo_web_environment):
    _, run_name = demo_web_environment
    launch_resp = client.post(f"/api/runs/{run_name}/launch", json={})
    job_id = launch_resp.json()["job_id"]

    jobs = client.get("/api/jobs").json()["jobs"]
    ids = [j["job_id"] for j in jobs]
    assert job_id in ids


# ---------------------------------------------------------------------------
# GET /api/jobs/{job_id}
# ---------------------------------------------------------------------------

def test_get_job_unknown_returns_404(client, demo_web_environment):
    resp = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
