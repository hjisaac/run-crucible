from __future__ import annotations

import ast
import logging
import sys
from textwrap import dedent
from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner

import interface.cli.cli as ui_cli
import interface.cli.utils as ui_utils
from core.runtime import context as runtime_context
from omegaconf import OmegaConf


def _clear_runs_modules() -> None:
	for module_name in list(sys.modules):
		if module_name == "runs" or module_name.startswith("runs."):
			del sys.modules[module_name]


__RUNNER_SOURCE = dedent(
	"""
	from core.jobs import AbstractJob

	class Job(AbstractJob):
	    def setup_data(self) -> None:
	        self.data = {'message': self.config['message']}

	    def run(self) -> dict[str, str]:
	        self.setup()
	        return {
	            'status': 'ok',
	            'message': self.data['message'],
	            'log_dir': self.config['log_dir'],
	        }

	JOB_CLASS = Job
	"""
)


def _write_demo_run_package(tmp_path: Path) -> Path:
	runs_root = tmp_path / "runs"
	run_dir = runs_root / "demo"
	config_dir = run_dir / "configs"
	config_dir.mkdir(parents=True)

	(runs_root / "__init__.py").write_text("", encoding="utf-8")
	(run_dir / "__init__.py").write_text(
		"from .runner import Job, JOB_CLASS\n"
		"__all__ = ['Job', 'JOB_CLASS']\n",
		encoding="utf-8",
	)
	(run_dir / "runner.py").write_text(__RUNNER_SOURCE, encoding="utf-8")

	log_dir = tmp_path / "runtime-logs"
	(config_dir / "default.yaml").write_text(
		dedent(
			f"""
			log_dir: {log_dir.as_posix()}
			log_console_level: INFO
			log_file_level: DEBUG
			message: base
			"""
		).lstrip(),
		encoding="utf-8",
	)

	return runs_root


def _assert_generated_package_is_valid(created: Path) -> None:
	ast.parse((created / "__init__.py").read_text(encoding="utf-8"))
	ast.parse((created / "runner.py").read_text(encoding="utf-8"))
	OmegaConf.create((created / "configs" / "default.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def demo_run_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	runs_root = _write_demo_run_package(tmp_path)
	monkeypatch.syspath_prepend(str(tmp_path))
	monkeypatch.setattr(runtime_context, "RUNS_ROOT", runs_root)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	_clear_runs_modules()
	return tmp_path


def test_run_named_job_loads_config_applies_overrides_and_logs(demo_run_environment: Path, caplog) -> None:
	tmp_path = demo_run_environment

	with caplog.at_level(logging.WARNING, logger="core.runtime.execution"):
		result = ui_utils.run_named_job("demo", "default", overrides=["message=overridden"])

	assert result == {
		"status": "ok",
		"message": "overridden",
		"log_dir": str((tmp_path / "runtime-logs").as_posix()),
	}
	assert "Runtime config for run='demo'" in caplog.text
	assert "overrides=message=overridden" in caplog.text
	assert "message: overridden" in caplog.text


def test_cli_command_runs_temp_pipeline_with_config_and_override(demo_run_environment: Path) -> None:

	app = Typer()
	app.command(name="demo")(ui_cli._build_run_command("demo"))

	runner = CliRunner()
	result = runner.invoke(app, ["--config", "default", "-o", "message=from_cli"])

	assert result.exit_code == 0
	assert "from_cli" in result.output
	assert "status" in result.output


def test_list_available_runs_reads_temp_runs_folder(tmp_path, monkeypatch) -> None:
	runs_root = _write_demo_run_package(tmp_path)
	monkeypatch.setattr(runtime_context, "RUNS_ROOT", runs_root)

	assert ui_utils.list_available_runs() == ["demo"]


def test_create_run_package_standalone_creates_expected_structure(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	created = ui_utils.create_run_package("vision_mlp", standalone=True)

	assert created == runs_root / "vision_mlp"
	assert (created / "__init__.py").exists()
	assert (created / "runner.py").exists()
	assert (created / "README.md").exists()
	assert (created / "configs" / "default.yaml").exists()

	init_source = (created / "__init__.py").read_text(encoding="utf-8")
	assert "from .runner import JOB_CLASS, Job" in init_source
	assert '__all__ = ["Job", "JOB_CLASS"]' in init_source

	runner_source = (created / "runner.py").read_text(encoding="utf-8")
	assert "class Job(AbstractJob):" in runner_source
	assert 'return {"status": "ok", "task": "vision_mlp", "mode": "standalone"}' in runner_source

	config_source = (created / "configs" / "default.yaml").read_text(encoding="utf-8")
	assert "log_dir: logs" in config_source
	assert "log_console_level: INFO" in config_source
	assert "log_file_level: DEBUG" in config_source
	_assert_generated_package_is_valid(created)


def test_create_run_package_training_creates_expected_structure(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	created = ui_utils.create_run_package("vision_trainer", standalone=False)

	runner_source = (created / "runner.py").read_text(encoding="utf-8")
	assert "class Job(AbstractTrainerJob):" in runner_source
	assert 'return {"status": "ok", "task": "vision_trainer", "mode": "training"}' in runner_source
	_assert_generated_package_is_valid(created)


def test_create_run_package_normalizes_name_to_lowercase(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	created = ui_utils.create_run_package("Vision_MLP", standalone=True)

	assert created == runs_root / "vision_mlp"
	assert created.exists()


def test_create_run_package_rejects_reserved_name(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	with pytest.raises(ValueError, match="reserved by the CLI"):
		ui_utils.create_run_package("create", standalone=True)


def test_create_run_package_force_overwrites_files(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	created = ui_utils.create_run_package("vision_force", standalone=True)
	(created / "runner.py").write_text("sentinel\n", encoding="utf-8")

	ui_utils.create_run_package("vision_force", standalone=False, force=True)

	runner_source = (created / "runner.py").read_text(encoding="utf-8")
	assert "AbstractTrainerJob" in runner_source
	_assert_generated_package_is_valid(created)


def test_cli_create_command_creates_standalone_scaffold(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	runs_root.mkdir(parents=True)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["create", "demo_new", "--job-type", "standalone"])

	assert result.exit_code == 0
	assert "Created run scaffold:" in result.output
	assert (runs_root / "demo_new" / "runner.py").exists()
	assert "AbstractJob" in (runs_root / "demo_new" / "runner.py").read_text(encoding="utf-8")
	_assert_generated_package_is_valid(runs_root / "demo_new")


def test_cli_create_command_creates_training_scaffold(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	runs_root.mkdir(parents=True)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["create", "demo_train", "--job-type", "training"])

	assert result.exit_code == 0
	assert "Created run scaffold:" in result.output
	assert (runs_root / "demo_train" / "runner.py").exists()
	assert "AbstractTrainerJob" in (runs_root / "demo_train" / "runner.py").read_text(encoding="utf-8")
	_assert_generated_package_is_valid(runs_root / "demo_train")


def test_cli_create_command_defaults_to_standalone(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	runs_root.mkdir(parents=True)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["create", "demo_default"])

	assert result.exit_code == 0
	assert "AbstractJob" in (runs_root / "demo_default" / "runner.py").read_text(encoding="utf-8")
	assert "AbstractTrainerJob" not in (runs_root / "demo_default" / "runner.py").read_text(encoding="utf-8")
	_assert_generated_package_is_valid(runs_root / "demo_default")


def test_cli_create_command_accepts_case_insensitive_job_type(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	runs_root.mkdir(parents=True)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["create", "demo_caps", "--job-type", "TRAINING"])

	assert result.exit_code == 0
	assert "AbstractTrainerJob" in (runs_root / "demo_caps" / "runner.py").read_text(encoding="utf-8")
	_assert_generated_package_is_valid(runs_root / "demo_caps")


def test_cli_create_command_rejects_reserved_name(tmp_path, monkeypatch) -> None:
	runs_root = tmp_path / "runs"
	runs_root.mkdir(parents=True)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["create", "run"])

	assert result.exit_code != 0
	assert "reserved by the CLI" in result.output


def test_cli_run_subcommand_forwards_args(monkeypatch) -> None:
	captured: dict[str, object] = {}

	def _fake_run_named_job(run_name: str, config_name: str, overrides: list[str] | None = None):
		captured["run_name"] = run_name
		captured["config_name"] = config_name
		captured["overrides"] = overrides
		return {"status": "ok"}

	monkeypatch.setattr(ui_cli, "run_named_job", _fake_run_named_job)

	runner = CliRunner()
	result = runner.invoke(ui_cli.app, ["run", "demo", "--config", "default", "-o", "a=b", "-o", "c=d"])

	assert result.exit_code == 0
	assert captured == {
		"run_name": "demo",
		"config_name": "default",
		"overrides": ["a=b", "c=d"],
	}
	assert "status" in result.output