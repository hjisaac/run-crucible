# run-crucible

Composable Python job runner with dynamic job discovery, Hydra config overrides, and a Typer CLI.

## What This Project Is

`run-crucible` is a lightweight framework for organizing and running modular "runs" under the `runs/` directory.

Each run package provides:

- A concrete job class (`Job` or `JOB_CLASS`) derived from `AbstractJob`
- A config folder (`configs/`) with YAML configs
- Optional run-specific logic, models, and training behavior

The CLI auto-discovers available runs and executes them with config and override support.

## Highlights

- Dynamic run discovery from `runs/<name>/`
- Typer-based CLI via `crucible`
- Hydra-powered config loading and runtime overrides
- Per-run logging to console and file
- Base abstractions for standalone and training jobs
- Test coverage for CLI + pipeline wiring

## Requirements

- Python 3.13+
- uv

## Installation

Install dependencies and the project environment with uv.

```bash
uv sync
```

## CLI Usage

List available runs:

```bash
uv run crucible list
```

Run a discovered job (example: `mlp`):

```bash
uv run crucible run mlp
```

Run with config and Hydra-style overrides:

```bash
uv run crucible run mlp --config default -o log_console_level=DEBUG -o log_dir=logs/dev
```

Backward-compatible direct run commands (for example `uv run crucible mlp`) are still supported.

You can also run via module:

```bash
uv run python -m interface.cli
```

## How It Works

1. The CLI scans `runs/` for package folders containing `__init__.py`.
2. For each discovered run, it registers a command with the same name.
3. At runtime, it resolves `JOB_CLASS` or `Job` from `runs.<run_name>`.
4. It loads `runs/<run_name>/configs/<config>.yaml` using Hydra.
5. Overrides passed by `-o/--override` are applied.
6. The job is instantiated and executed.

## Project Structure

```text
core/
	jobs/            # Abstract job interfaces
		abstract.py
		standalone.py
		training.py
	runtime/         # Run discovery and execution orchestration
		discovery.py
		execution.py
		context.py
	config/          # Config loading and override utilities
		loader.py
		overrides.py
	handlers/        # Runtime handlers (logging, I/O, etc.)
		logger.py
	trackers/        # Experiment tracker interfaces and implementations
		abstract.py
		wandb.py

plugins/
	ml/              # Optional ML plugin modules
		datasets/
		models/
		losses/
		optimizers/
		schedulers/

runs/
	mlp/             # Example run package
		__init__.py
		runner.py
		configs/
			default.yaml
		outputs/

interface/
	cli/
		cli.py          # Typer app entrypoint
		utils.py        # CLI scaffolding and template helpers

tests/
	test_interface_cli_pipeline.py
```

## Create a New Run

Use the create command:

```bash
uv run crucible create my_experiment --job-type standalone
```

Or scaffold a training job:

```bash
uv run crucible create my_experiment --job-type training
```

Templates are file-based under `interface/cli/templates/`, so you can customize scaffold output without editing CLI code.

This creates:

- `runs/my_experiment/__init__.py`
- `runs/my_experiment/runner.py`
- `runs/my_experiment/README.md`
- `runs/my_experiment/configs/default.yaml`
- `runs/my_experiment/outputs/`

You can overwrite existing scaffold files with:

```bash
uv run crucible create my_experiment --job-type standalone --force
```

Manual setup is still supported.

Add a package under `runs/`, for example `runs/my_experiment/`:

1. Create `runs/my_experiment/__init__.py`
2. Create `runs/my_experiment/runner.py` with a concrete `AbstractJob` subclass
3. Export `Job` or `JOB_CLASS` from `__init__.py`
4. Add `runs/my_experiment/configs/default.yaml`

Minimal pattern:

```python
from core.jobs import AbstractJob


class Job(AbstractJob):
		def setup_data(self) -> None:
				self.data = {"status": "ready"}

		def run(self):
				self.setup()
				return {"status": "ok"}


JOB_CLASS = Job
```

After that, your run should appear automatically in:

```bash
uv run crucible list
```

## Testing

Run tests with:

```bash
uv run pytest
```

## Notes

- Runtime logging settings are read from config keys like `log_dir`, `log_console_level`, and `log_file_level`.
- The project includes a Weights & Biases tracker abstraction in `core/trackers/wandb.py` for experiment tracking integration.
