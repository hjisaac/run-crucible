

import tempfile
from pathlib import Path
import pytest
from crucible.core.config.loader import load_run_config
from crucible.core.config import loader
from crucible.core import constants

# YAML constants for test configs
_ROOT_CONFIG_YAML = '''
log_dir: logs_root
log_level: INFO
'''

_SUBCONFIG_OVERRIDE_YAML = '''
log_dir: logs_sub
'''

def test_subconfig_overrides_root(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Write root config
        root_config = tmp / loader.ROOT_CONFIG_FILENAME
        root_config.write_text(_ROOT_CONFIG_YAML)
        # Write run config
        run_dir = tmp / "my_runs" / "exp1" / "configs"
        run_dir.mkdir(parents=True)
        sub_config = run_dir / "default.yaml"
        sub_config.write_text(_SUBCONFIG_OVERRIDE_YAML)
        # Patch loader and constants to use this workspace
        monkeypatch.setattr(constants, "RUNS_ROOT", tmp / "my_runs")
        monkeypatch.setattr(loader, "RUNS_ROOT", tmp / "my_runs")
        # Patch __file__ to simulate loader location
        monkeypatch.setattr("crucible.core.config.loader.__file__", str(tmp / "crucible" / "core" / "config" / "loader.py"))
        monkeypatch.setattr(loader, "ROOT_CONFIG_FILENAME", root_config.name)
        # Run loader
        config, _, _ = load_run_config("exp1", "default")
        assert config["log_dir"] == "logs_sub"
        assert config["log_level"] == "INFO"

def test_root_config_used_if_subconfig_missing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Write root config
        root_config = tmp / loader.ROOT_CONFIG_FILENAME
        root_config.write_text(_ROOT_CONFIG_YAML)
        # Write run config (no log_level)
        run_dir = tmp / "my_runs" / "exp2" / "configs"
        run_dir.mkdir(parents=True)
        sub_config = run_dir / "default.yaml"
        sub_config.write_text(_SUBCONFIG_OVERRIDE_YAML)
        # Patch loader and constants to use this workspace
        monkeypatch.setattr(constants, "RUNS_ROOT", tmp / "my_runs")
        monkeypatch.setattr(loader, "RUNS_ROOT", tmp / "my_runs")
        # Patch __file__ to simulate loader location
        monkeypatch.setattr("crucible.core.config.loader.__file__", str(tmp / "crucible" / "core" / "config" / "loader.py"))
        monkeypatch.setattr(loader, "ROOT_CONFIG_FILENAME", root_config.name)
        # Run loader
        config, _, _ = load_run_config("exp2", "default")
        assert config["log_dir"] == "logs_sub"
        assert config["log_level"] == "INFO"
