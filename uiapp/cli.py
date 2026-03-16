from __future__ import annotations

from typing import Any

import typer

from uiapp.utils import list_available_runs, run_named_job


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


def main() -> None:
	app()