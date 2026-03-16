from __future__ import annotations

import logging
import sys
from pathlib import Path

from typer import Typer
from typer.testing import CliRunner

import uiapp.cli as ui_cli
import uiapp.utils as ui_utils


def _clear_runs_modules() -> None:
	for module_name in list(sys.modules):
		if module_name == "runs" or module_name.startswith("runs."):
			del sys.modules[module_name]


def _write_temp_run_package(tmp_path: Path) -> Path:
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
	(run_dir / "runner.py").write_text(
		"from core.jobs import AbstractJob\n"
		"\n"
		"class Job(AbstractJob):\n"
		"    def setup_data(self) -> None:\n"
		"        self.data = {'message': self.config['message']}\n"
		"\n"
		"    def run(self) -> dict[str, str]:\n"
		"        self.setup()\n"
		"        return {\n"
		"            'status': 'ok',\n"
		"            'message': self.data['message'],\n"
		"            'log_dir': self.config['log_dir'],\n"
		"        }\n"
		"\n"
		"JOB_CLASS = Job\n",
		encoding="utf-8",
	)

	log_dir = tmp_path / "runtime-logs"
	(config_dir / "default.yaml").write_text(
		"log_dir: " + str(log_dir.as_posix()) + "\n"
		"log_console_level: INFO\n"
		"log_file_level: DEBUG\n"
		"message: base\n",
		encoding="utf-8",
	)

	return runs_root


def test_run_named_job_loads_config_applies_overrides_and_logs(tmp_path, monkeypatch, caplog) -> None:
	runs_root = _write_temp_run_package(tmp_path)
	monkeypatch.syspath_prepend(str(tmp_path))
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	_clear_runs_modules()

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


def test_cli_command_runs_temp_pipeline_with_config_and_override(tmp_path, monkeypatch) -> None:
	runs_root = _write_temp_run_package(tmp_path)
	monkeypatch.syspath_prepend(str(tmp_path))
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)
	_clear_runs_modules()

	app = Typer()
	app.command(name="demo")(ui_cli._build_run_command("demo"))

	runner = CliRunner()
	result = runner.invoke(app, ["demo", "--config", "default", "-o", "message=from_cli"])

	assert result.exit_code == 0
	assert "from_cli" in result.output
	assert "status" in result.output


def test_list_available_runs_reads_temp_runs_folder(tmp_path, monkeypatch) -> None:
	runs_root = _write_temp_run_package(tmp_path)
	monkeypatch.setattr(ui_utils, "RUNS_ROOT", runs_root)

	assert ui_utils.list_available_runs() == ["demo"]