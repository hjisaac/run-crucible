from __future__ import annotations

import ast
import importlib
import inspect
import logging
import re
from pathlib import Path
from typing import Any

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from core.jobs import AbstractJob

logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_EXTENSIONS = (".yaml", ".yml")
RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
RUN_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _normalize_run_name(run_name: str) -> str:
	normalized = run_name.strip().lower()
	if not normalized:
		raise ValueError("Run name cannot be empty.")
	if normalized in {"list", "run", "create"}:
		raise ValueError(f"Run name '{normalized}' is reserved by the CLI.")
	if not RUN_NAME_PATTERN.match(normalized):
		raise ValueError(
			"Run name must match ^[a-z][a-z0-9_]*$ (lowercase letters, numbers, underscore)."
		)
	return normalized


def _write_scaffold_file(path: Path, content: str, force: bool) -> None:
	if path.exists() and not force:
		raise FileExistsError(f"File already exists: {path}")
	path.write_text(content, encoding="utf-8")


def _render_template(template_name: str, **kwargs: str) -> str:
	template_path = TEMPLATES_DIR / template_name
	if not template_path.exists():
		raise FileNotFoundError(f"Template file was not found: {template_path}")
	template = template_path.read_text(encoding="utf-8")
	return template.format(**kwargs)


def _validate_rendered_template(template_name: str, rendered_content: str) -> None:
	try:
		if template_name.endswith(".py.tpl"):
			ast.parse(rendered_content)
		elif template_name.endswith((".yaml.tpl", ".yml.tpl")):
			OmegaConf.create(rendered_content)
	except SyntaxError as exc:
		raise ValueError(f"Rendered template '{template_name}' is not valid Python.") from exc
	except Exception as exc:
		raise ValueError(f"Rendered template '{template_name}' is not valid YAML.") from exc


def create_run_package(run_name: str, *, standalone: bool = True, force: bool = False) -> Path:
	run_name = _normalize_run_name(run_name)
	run_dir = RUNS_ROOT / run_name

	if run_dir.exists() and not force:
		raise FileExistsError(f"Run folder already exists: {run_dir}")

	configs_dir = run_dir / "configs"
	configs_dir.mkdir(parents=True, exist_ok=True)
	runner_template_name = "runner_standalone.py.tpl" if standalone else "runner_training.py.tpl"
	runner_source = _render_template(runner_template_name, run_name=run_name)

	_validate_rendered_template(runner_template_name, runner_source)

	init_source = _render_template("__init__.py.tpl")
	_validate_rendered_template("__init__.py.tpl", init_source)

	default_config_source = _render_template("default.yaml.tpl")
	_validate_rendered_template("default.yaml.tpl", default_config_source)

	_write_scaffold_file(run_dir / "__init__.py", init_source, force)
	_write_scaffold_file(run_dir / "runner.py", runner_source, force)
	_write_scaffold_file(run_dir / "README.md", "", force)
	_write_scaffold_file(
		configs_dir / "default.yaml",
		default_config_source,
		force,
	)

	return run_dir


def list_available_runs() -> list[str]:
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
	run_name = run_name.strip().lower()
	try:
		module = importlib.import_module(f"runs.{run_name}")
	except ModuleNotFoundError as exc:
		raise ValueError(f"Run '{run_name}' was not found.") from exc

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
		f"Run '{run_name}' does not expose a concrete job class. "
		"Export Job or JOB_CLASS from runs/<run>/__init__.py."
	)


def _resolve_config_path(run_name: str, config_name: str) -> tuple[Path, str, Path]:
	run_dir = RUNS_ROOT / run_name
	if not run_dir.exists():
		raise FileNotFoundError(f"Run folder was not found: {run_dir}")

	config_dir = run_dir / "configs"
	if not config_dir.exists():
		raise FileNotFoundError(f"Config folder was not found: {config_dir}")

	requested_path = Path(config_name)
	if requested_path.suffix and requested_path.suffix not in SUPPORTED_CONFIG_EXTENSIONS:
		raise ValueError(
			"Only YAML configs are supported. Use .yaml/.yml or pass the config name without extension."
		)

	config_stem = requested_path.stem if requested_path.suffix else config_name.strip()
	candidates = [config_dir / f"{config_stem}{extension}" for extension in SUPPORTED_CONFIG_EXTENSIONS]
	resolved = next((path for path in candidates if path.exists()), None)
	if resolved is None:
		looked_up = ", ".join(path.name for path in candidates)
		raise FileNotFoundError(
			f"Config '{config_name}' was not found for run '{run_name}'. Looked for: {looked_up}"
		)

	return config_dir, config_stem, resolved


def _sanitize_overrides(overrides: list[str] | None) -> list[str]:
	if not overrides:
		return []

	return [item.strip() for item in overrides if item and item.strip()]


def load_run_config(
	run_name: str,
	config_name: str,
	overrides: list[str] | None = None,
) -> tuple[dict[str, Any], Path, list[str]]:
	run_name = run_name.strip().lower()
	config_dir, config_stem, config_path = _resolve_config_path(run_name, config_name)
	resolved_overrides = _sanitize_overrides(overrides)

	with initialize_config_dir(version_base=None, config_dir=str(config_dir.resolve())):
		config = compose(config_name=config_stem, overrides=resolved_overrides)

	resolved = OmegaConf.to_container(config, resolve=True)
	if not isinstance(resolved, dict):
		raise ValueError(f"Config '{config_name}' for run '{run_name}' must resolve to a dictionary.")
	return resolved, config_path, resolved_overrides


def _log_runtime_config(run_name: str, config_path: Path, config: dict[str, Any], overrides: list[str]) -> None:
	overrides_display = ", ".join(overrides) if overrides else "none"
	config_yaml = OmegaConf.to_yaml(OmegaConf.create(config), resolve=True)
	logger.warning(
		"Runtime config for run='%s' from '%s' | overrides=%s\n%s",
		run_name,
		config_path,
		overrides_display,
		config_yaml,
	)


def run_named_job(run_name: str, config_name: str, overrides: list[str] | None = None) -> Any:
	job_class = resolve_job_class(run_name)
	config, config_path, resolved_overrides = load_run_config(run_name, config_name, overrides=overrides)
	_log_runtime_config(run_name, config_path, config, resolved_overrides)
	job = job_class(config=config)
	return job.run()