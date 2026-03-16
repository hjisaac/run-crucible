from __future__ import annotations

import logging
import sys
from textwrap import dedent
from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner

import uiapp.cli as ui_cli
import uiapp.utils as ui_utils


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


@pytest.fixture
def demo_run_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	runs_root = _write_demo_run_package(tmp_path)
	monkeypatch.syspath_prepend(str(tmp_path))
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	_clear_runs_modules()
	return tmp_path


def test_run_named_job_loads_config_applies_overrides_and_logs(demo_run_environment: Path, caplog) -> None:
	tmp_path = demo_run_environment

	with caplog.at_level(logging.WARNING, logger="uiapp.utils"):
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
	result = runner.invoke(app, ["demo", "--config", "default", "-o", "message=from_cli"])

	assert result.exit_code == 0
	assert "from_cli" in result.output
	assert "status" in result.output


def test_list_available_runs_reads_temp_runs_folder(tmp_path, monkeypatch) -> None:
	runs_root = _write_demo_run_package(tmp_path)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	assert ui_utils.list_available_runs() == ["demo"]