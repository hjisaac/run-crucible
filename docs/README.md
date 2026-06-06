# Crucible

Composable Python job runner with dynamic job discovery, Hydra config overrides, and a Typer CLI.

## Vocabulary

Crucible uses three words, each with exactly one meaning:

- **Job** — the unit of work you author: a Python package under `jobs/<name>/` containing a `Job` class. This is what you write and what gets discovered.
- **Run** — a single execution of a job. Each run gets a unique `run_id` (timestamped) and its own log file. (This matches the "run" concept in tools like Weights & Biases.)
- **`run`** (the CLI verb) — start a run of a job.

So: *you author a **job**; each time you execute it you get a **run**.* Reusable ML building blocks (models, optimizers, schedulers) live in `crucible/plugins/ml/` and are never jobs themselves.

## What This Project Is

`Crucible` is a lightweight framework for organizing and running jobs under the `jobs/` directory.

## How to Create and Use Jobs

All user jobs live in the `jobs/` folder. Each job is a Python package with:

- A concrete job class (`Job` or `JOB_CLASS`) derived from `AbstractJob` (see example below)
- A `configs/` folder with YAML configs (e.g., `default.yaml`)
- Optional job-specific logic, models, and training behavior

The CLI auto-discovers available jobs in `jobs/` and executes them with config and override support.

## Highlights

- Dynamic job discovery from `jobs/<name>/`
- Typer-based CLI via `crucible`
- Hydra-powered config loading and runtime overrides
- Per-run logging to console and file
- Base abstractions for plain jobs and trainer jobs
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

List available jobs:

```bash
uv run crucible list
```

Start a run of a discovered job (example: `mlp`):

```bash
uv run crucible run mlp
```

Run with config and Hydra-style overrides:

```bash
uv run crucible run mlp --config default -o log_console_level=DEBUG -o log_dir=logs/dev
```

Backward-compatible direct commands (for example `uv run crucible mlp`) are still supported.

You can also run via module:

```bash
uv run python -m interface.cli
```

## How It Works

1. The CLI scans `jobs/` for package folders containing `__init__.py`.
2. For each discovered job, it registers a command with the same name.
3. At runtime, it resolves `JOB_CLASS` or `Job` from `jobs.<job_name>`.
4. It loads `jobs/<job_name>/configs/<config>.yaml` using Hydra.
5. Overrides passed by `-o/--override` are applied.
6. The job is instantiated and executed, producing one run.

## More About the Framework

If you are interested in the internal code structure, see [crucible/README.md](../crucible/README.md).

## Create a New Job

Use the create command:

```bash
uv run crucible create my_experiment --kind job
```

Or scaffold a trainer job (ML training loop):

```bash
uv run crucible create my_experiment --kind trainer
```

Templates are file-based under `crucible/interface/cli/templates/`, so you can customize scaffold output without editing CLI code.

This creates:

- `jobs/my_experiment/__init__.py`
- `jobs/my_experiment/job.py`
- `jobs/my_experiment/README.md`
- `jobs/my_experiment/configs/default.yaml`
- `jobs/my_experiment/outputs/`

You can overwrite existing scaffold files with:

```bash
uv run crucible create my_experiment --kind job --force
```

Manual setup is still supported. Add a package under `jobs/`, for example `jobs/my_experiment/`:

1. Create `jobs/my_experiment/__init__.py`
2. Create `jobs/my_experiment/job.py` with a concrete `AbstractJob` subclass
3. Export `Job` or `JOB_CLASS` from `__init__.py`
4. Add `jobs/my_experiment/configs/default.yaml`

Minimal pattern:

```python
from crucible.core.jobs import AbstractJob


class Job(AbstractJob):
    def setup_data(self) -> None:
        self.data = {"status": "ready"}

    def run(self):
        self.setup()
        return {"status": "ok"}


JOB_CLASS = Job
```

After that, your job should appear automatically in:

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
- The project includes a Weights & Biases tracker abstraction in `crucible/core/trackers/wandb.py` for experiment tracking integration.
