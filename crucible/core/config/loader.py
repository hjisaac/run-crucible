from __future__ import annotations

from pathlib import Path
from typing import Any

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf, OmegaConf

from crucible.core.config.overrides import sanitize_overrides
from crucible.core.constants import RUNS_ROOT, SUPPORTED_CONFIG_EXTENSIONS, ROOT_CONFIG_FILENAME


def _resolve_config_path(run_name: str, config_name: str) -> tuple[Path, str, Path]:
    run_dir = RUNS_ROOT / run_name
    if not run_dir.exists():
        raise FileNotFoundError(f"Run folder was not found: {run_dir}")

    config_dir = run_dir / "configs"
    if not config_dir.exists():
        raise FileNotFoundError(f"Config folder was not found: {config_dir}")

    requested_path = Path(config_name)
    if requested_path.suffix and requested_path.suffix not in SUPPORTED_CONFIG_EXTENSIONS:
        raise ValueError(
            "Only YAML configs are supported. Use .yaml/.yml or pass the config name without extension."
        )

    config_stem = requested_path.stem if requested_path.suffix else config_name.strip()
    candidates = [config_dir / f"{config_stem}{extension}" for extension in SUPPORTED_CONFIG_EXTENSIONS]
    resolved = next((path for path in candidates if path.exists()), None)
    if resolved is None:
        looked_up = ", ".join(path.name for path in candidates)
        raise FileNotFoundError(
            f"Config '{config_name}' was not found for run '{run_name}'. Looked for: {looked_up}"
        )

    return config_dir, config_stem, resolved


def load_run_config(
    run_name: str,
    config_name: str,
    overrides: list[str] | None = None,
) -> tuple[dict[str, Any], Path, list[str]]:
    """Load a run config from the runs root (default: my_runs)/<name>/configs, merging with root.config.yaml.
    Subconfig values override root config."""
    normalized_run_name = run_name.strip().lower()
    config_dir, config_stem, config_path = _resolve_config_path(normalized_run_name, config_name)
    resolved_overrides = sanitize_overrides(overrides)

    # Load root config (if present)

    root_config_path = Path(__file__).resolve().parents[3] / ROOT_CONFIG_FILENAME
    if root_config_path.exists():
        root_cfg = OmegaConf.load(str(root_config_path))
    else:
        root_cfg = OmegaConf.create({})

    # Load subconfig with Hydra
    with initialize_config_dir(version_base=None, config_dir=str(config_dir.resolve())):
        sub_cfg = compose(config_name=config_stem, overrides=resolved_overrides)

    # Merge: subconfig values take precedence
    merged_cfg = OmegaConf.merge(root_cfg, sub_cfg)
    resolved = OmegaConf.to_container(merged_cfg, resolve=True)
    if not isinstance(resolved, dict):
        raise ValueError(
            f"Config '{config_name}' for run '{normalized_run_name}' must resolve to a dictionary."
        )

    return resolved, config_path, resolved_overrides
