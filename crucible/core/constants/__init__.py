from pathlib import Path

# Name of the directory that holds user-authored jobs (can be changed for custom setups).
JOBS_ROOT_NAME = "jobs"

# Workspace-level jobs folder discovered by the runtime and CLI scaffolding.
JOBS_ROOT = Path(__file__).resolve().parents[3] / JOBS_ROOT_NAME
SUPPORTED_CONFIG_EXTENSIONS = (".yaml", ".yml")

# Constant for the root config filename
ROOT_CONFIG_FILENAME = "root.config.yaml"
