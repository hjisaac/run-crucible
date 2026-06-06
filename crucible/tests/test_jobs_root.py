import os
import tempfile
from pathlib import Path
import pytest
from crucible.core.constants import RUNS_ROOT_NAME, RUNS_ROOT
import crucible.core.constants as constants
from crucible.interface.cli import utils as cli_utils

def test_runs_root_name_constant_default():
    assert RUNS_ROOT_NAME == "my_runs"
    assert RUNS_ROOT.name == RUNS_ROOT_NAME

def test_create_run_package_creates_runs_root(tmp_path, monkeypatch):
    # Change RUNS_ROOT and RUNS_ROOT_NAME to a temp dir
    monkeypatch.setattr(constants, "RUNS_ROOT_NAME", "custom_runs")
    custom_root = tmp_path / "custom_runs"
    monkeypatch.setattr(constants, "RUNS_ROOT", custom_root)
    monkeypatch.setattr(cli_utils, "RUNS_ROOT", custom_root)
    # Remove if exists
    if custom_root.exists():
        for child in custom_root.iterdir():
            if child.is_dir():
                for sub in child.iterdir():
                    sub.unlink()
                child.rmdir()
            else:
                child.unlink()
        custom_root.rmdir()
    assert not custom_root.exists()
    # Should create the root and the run dir
    run_dir = cli_utils.create_run_package("test_exp", force=True)
    assert custom_root.exists()
    assert (custom_root / "test_exp").exists()
    assert (custom_root / "test_exp" / "configs").exists()
    assert (custom_root / "test_exp" / "outputs").exists()

def test_create_run_package_does_not_remove_existing_runs_root(tmp_path, monkeypatch):
    # Setup: create a custom runs root with a pre-existing subfolder
    monkeypatch.setattr(constants, "RUNS_ROOT_NAME", "custom_runs")
    custom_root = tmp_path / "custom_runs"
    monkeypatch.setattr(constants, "RUNS_ROOT", custom_root)
    monkeypatch.setattr(cli_utils, "RUNS_ROOT", custom_root)
    custom_root.mkdir(parents=True, exist_ok=True)
    preexisting = custom_root / "preexisting_run_folder"
    preexisting.mkdir()
    (preexisting / "keep.txt").write_text("keep this file")
    # Act: create a new run package
    cli_utils.create_run_package("test_exp2", force=True)
    # Assert: preexisting subfolder and file are untouched
    assert preexisting.exists()
    assert (preexisting / "keep.txt").exists()
    assert (custom_root / "test_exp2").exists()
    assert (custom_root / "test_exp2" / "configs").exists()
    assert (custom_root / "test_exp2" / "outputs").exists()
