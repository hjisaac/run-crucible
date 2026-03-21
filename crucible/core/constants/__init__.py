from pathlib import Path

# Name of the runs directory (can be changed for custom setups)
RUNS_ROOT_NAME = "my_runs"

# Workspace-level runs folder discovered by runtime and CLI scaffolding.
RUNS_ROOT = Path(__file__).resolve().parents[3] / RUNS_ROOT_NAME
SUPPORTED_CONFIG_EXTENSIONS = (".yaml", ".yml")

# Constant for the root config filename
ROOT_CONFIG_FILENAME = "root.config.yaml"
