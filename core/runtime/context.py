from pathlib import Path

# Workspace-level runs folder discovered by runtime and CLI scaffolding.
RUNS_ROOT = Path(__file__).resolve().parents[2] / "runs"
SUPPORTED_CONFIG_EXTENSIONS = (".yaml", ".yml")
