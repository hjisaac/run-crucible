from __future__ import annotations

import ast
import re
from pathlib import Path

from omegaconf import OmegaConf

from core.runtime.context import RUNS_ROOT
from core.runtime.discovery import list_available_runs
from core.runtime.execution import run_named_job

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
	outputs_dir = run_dir / "outputs"
	configs_dir.mkdir(parents=True, exist_ok=True)
	outputs_dir.mkdir(parents=True, exist_ok=True)
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