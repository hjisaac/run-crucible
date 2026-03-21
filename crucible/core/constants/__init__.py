from pathlib import Path

# Workspace-level runs folder discovered by runtime and CLI scaffolding.
RUNS_ROOT = Path(__file__).resolve().parents[3] / "my_runs"
SUPPORTED_CONFIG_EXTENSIONS = (".yaml", ".yml")

# Constant for the root config filename
ROOT_CONFIG_FILENAME = "root.config.yaml"
