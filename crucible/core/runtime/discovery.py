from __future__ import annotations

import importlib
import inspect
from typing import Any

from core.jobs import AbstractJob
from core.constants import RUNS_ROOT


def list_available_runs() -> list[str]:
    """Return discovered run package names under runs/."""
    return sorted(
        path.name
        for path in RUNS_ROOT.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    )


def _resolve_job_class(module: Any) -> type[AbstractJob] | None:
    job_class = getattr(module, "JOB_CLASS", None)
    if inspect.isclass(job_class) and issubclass(job_class, AbstractJob):
        if inspect.isabstract(job_class):
            raise ValueError("JOB_CLASS is abstract; expose a concrete class.")
        return job_class

    default_job_class = getattr(module, "Job", None)
    if inspect.isclass(default_job_class) and issubclass(default_job_class, AbstractJob):
        if inspect.isabstract(default_job_class):
            raise ValueError("Job is abstract; expose a concrete class.")
        return default_job_class

    return None


def resolve_job_class(run_name: str) -> type[AbstractJob]:
    """Resolve a concrete job class from runs.<run_name>."""
    normalized_run_name = run_name.strip().lower()
    try:
        module = importlib.import_module(f"runs.{normalized_run_name}")
    except ModuleNotFoundError as exc:
        raise ValueError(f"Run '{normalized_run_name}' was not found.") from exc

    resolved = _resolve_job_class(module)
    if resolved is not None:
        return resolved

    for _, candidate in inspect.getmembers(module, inspect.isclass):
        if candidate.__module__ != module.__name__:
            continue
        if candidate is AbstractJob:
            continue
        if issubclass(candidate, AbstractJob) and not inspect.isabstract(candidate):
            return candidate

    raise ValueError(
        f"Run '{normalized_run_name}' does not expose a concrete job class. "
        "Export Job or JOB_CLASS from runs/<run>/__init__.py."
    )
