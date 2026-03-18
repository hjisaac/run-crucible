from __future__ import annotations

from enum import Enum
from typing import Any

import typer

from uiapp.utils import create_run_package, list_available_runs, run_named_job


class JobType(str, Enum):
	standalone = "standalone"
	training = "training"


app = typer.Typer(
	no_args_is_help=True,
	help="Run crucible jobs discovered under runs/.",
	pretty_exceptions_enable=False,
)


def _run_command(run_name: str, config: str = "default", overrides: list[str] | None = None) -> None:
	result = run_named_job(run_name, config, overrides=overrides)
	if result is not None:
		typer.echo(result)


def _build_run_command(run_name: str) -> Any:
	def command(
		config: str = typer.Option(
			"default",
			"--config",
			"-c",
			help="YAML config name under runs/<run>/configs, with or without extension.",
		),
		overrides: list[str] = typer.Option(
			None,
			"--override",
			"-o",
			help="Hydra-style override(s), e.g. -o trainer.lr=1e-3 (repeat flag for multiple).",
		),
	) -> None:
		"""Run a discovered crucible job."""
		_run_command(run_name, config, overrides=overrides)

	command.__name__ = f"run_{run_name}"
	command.__doc__ = f"Run the {run_name} job."
	return command


for discovered_run in list_available_runs():
	app.command(name=discovered_run)(_build_run_command(discovered_run))


@app.command("list")
def list_runs() -> None:
	"""List discovered runs."""
	for run_name in list_available_runs():
		typer.echo(run_name)


@app.command("run")
def run_named(
	run_name: str = typer.Argument(..., help="Discovered run name (e.g. mlp)."),
	config: str = typer.Option(
		"default",
		"--config",
		"-c",
		help="YAML config name under runs/<run>/configs, with or without extension.",
	),
	overrides: list[str] = typer.Option(
		None,
		"--override",
		"-o",
		help="Hydra-style override(s), e.g. -o trainer.lr=1e-3 (repeat flag for multiple).",
	),
) -> None:
	"""Run a discovered crucible job by name."""
	_run_command(run_name, config, overrides=overrides)


def _create_run(
	run_name: str = typer.Argument(..., help="Run package name under runs/ (e.g. mlp_v2)."),
	job_type: JobType = typer.Option(
		JobType.standalone,
		"--job-type",
		help="Scaffold type: standalone or training.",
		case_sensitive=False,
	),
	force: bool = typer.Option(False, "--force", help="Overwrite scaffold files if they already exist."),
) -> None:
	"""Create a new run scaffold under runs/<name>/."""
	try:
		created = create_run_package(run_name, standalone=(job_type == JobType.standalone), force=force)
	except (ValueError, FileExistsError) as exc:
		raise typer.BadParameter(str(exc)) from exc

	typer.echo(f"Created run scaffold: {created}")


@app.command("create")
def create_run(
	run_name: str = typer.Argument(..., help="Run package name under runs/ (e.g. mlp_v2)."),
	job_type: JobType = typer.Option(
		JobType.standalone,
		"--job-type",
		help="Scaffold type: standalone or training.",
		case_sensitive=False,
	),
	force: bool = typer.Option(False, "--force", help="Overwrite scaffold files if they already exist."),
) -> None:
	"""Create a run package with starter files."""
	_create_run(run_name, job_type=job_type, force=force)


def main() -> None:
	app()