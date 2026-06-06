# Crucible Framework Code Structure

This document describes the internal structure of the `crucible/` folder, which contains all framework, plugin, and interface code for RunCrucible. This is intended for contributors and advanced users interested in the internals.

## crucible/
- `core/` — Core abstractions, runtime, config, job interfaces, trackers, and utilities
- `plugins/` — Optional ML modules (datasets, models, losses, optimizers, schedulers)
- `interface/` — CLI entrypoint, CLI utilities, and code generation templates
- `tests/` — Test suite for framework and CLI

### core/
- `jobs/` — Abstract job interfaces and base classes
- `runtime/` — Job discovery, run execution, and context management
- `config/` — Config loading and override logic
- `handlers/` — Logging and output handlers
- `trackers/` — Experiment tracking (e.g., Weights & Biases)
- `mixins/` — Optional mixins for job classes
- `utils/` — Shared utility functions

### plugins/ml/
- `datasets/`, `models/`, `losses/`, `optimizers/`, `schedulers/` — ML-specific modules

### interface/cli/
- `cli.py` — Typer CLI entrypoint
- `utils.py` — CLI helpers
- `templates/` — Code generation templates for new jobs

### tests/
- Framework and CLI tests

For details on how to use or extend the framework, see the main README or the relevant module docstrings.
