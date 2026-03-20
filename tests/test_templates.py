from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import interface.cli.utils as ui_utils

REAL_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "interface" / "cli" / "templates"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "templates"

SAMPLE_RUN_NAME = "test_run"


# ---------------------------------------------------------------------------
# Real templates: _validate_rendered_template must accept them without error.
# If someone commits a broken template this test will catch it.
# ---------------------------------------------------------------------------


def test_validate_accepts_standalone_runner_template() -> None:
	rendered = ui_utils._render_template("runner_standalone.py.tpl", run_name=SAMPLE_RUN_NAME)
	ui_utils._validate_rendered_template("runner_standalone.py.tpl", rendered)


def test_validate_accepts_training_runner_template() -> None:
	rendered = ui_utils._render_template("runner_training.py.tpl", run_name=SAMPLE_RUN_NAME)
	ui_utils._validate_rendered_template("runner_training.py.tpl", rendered)


def test_validate_accepts_init_template() -> None:
	rendered = ui_utils._render_template("__init__.py.tpl")
	ui_utils._validate_rendered_template("__init__.py.tpl", rendered)


def test_validate_accepts_default_yaml_template() -> None:
	rendered = ui_utils._render_template("default.yaml.tpl")
	ui_utils._validate_rendered_template("default.yaml.tpl", rendered)


# ---------------------------------------------------------------------------
# Broken fixture templates: _validate_rendered_template must reject them.
# Confirms the validator actually catches problems, not just silently passes.
# ---------------------------------------------------------------------------


def test_validate_rejects_broken_python_template() -> None:
	tpl = (FIXTURES_DIR / "broken_python.py.tpl").read_text(encoding="utf-8")
	rendered = tpl.format(run_name=SAMPLE_RUN_NAME)
	with pytest.raises(ValueError, match="not valid Python"):
		ui_utils._validate_rendered_template("runner_standalone.py.tpl", rendered)


def test_validate_rejects_broken_yaml_template() -> None:
	tpl = (FIXTURES_DIR / "broken_yaml.yaml.tpl").read_text(encoding="utf-8")
	with pytest.raises(ValueError, match="not valid YAML"):
		ui_utils._validate_rendered_template("default.yaml.tpl", tpl)


# ---------------------------------------------------------------------------
# Integration: create_run_package must call _validate_rendered_template.
# Proven by giving it a broken template and asserting no files are written.
# ---------------------------------------------------------------------------


def _build_template_dir(tmp_path: Path, *, replace: dict[str, Path]) -> Path:
	"""Copy real templates into tmp_path, swapping in broken fixtures by name."""
	tpl_dir = tmp_path / "templates"
	shutil.copytree(REAL_TEMPLATES_DIR, tpl_dir)
	for name, broken_path in replace.items():
		(tpl_dir / name).write_text(broken_path.read_text(encoding="utf-8"), encoding="utf-8")
	return tpl_dir


def test_create_run_package_fails_and_writes_nothing_on_broken_python_template(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	runs_root = tmp_path / "runs"
	tpl_dir = _build_template_dir(
		tmp_path, replace={"runner_standalone.py.tpl": FIXTURES_DIR / "broken_python.py.tpl"}
	)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	monkeypatch.setattr(ui_utils, "TEMPLATES_DIR", tpl_dir)

	with pytest.raises(ValueError, match="not valid Python"):
		ui_utils.create_run_package("my_exp", standalone=True)

	assert not (runs_root / "my_exp" / "runner.py").exists()


def test_create_run_package_fails_and_writes_nothing_on_broken_yaml_template(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	runs_root = tmp_path / "runs"
	tpl_dir = _build_template_dir(
		tmp_path, replace={"default.yaml.tpl": FIXTURES_DIR / "broken_yaml.yaml.tpl"}
	)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	monkeypatch.setattr(ui_utils, "TEMPLATES_DIR", tpl_dir)

	with pytest.raises(ValueError, match="not valid YAML"):
		ui_utils.create_run_package("my_exp", standalone=True)

	assert not (runs_root / "my_exp" / "configs" / "default.yaml").exists()
