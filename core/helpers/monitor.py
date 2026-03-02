"""
Tracker — unified experiment tracking interfaces.

Usage:
    tracker = WBTracker("muon_exp", project="ml-crucible")
    tracker.add_metrics(step=1, train_loss=0.42, val_acc=0.87)
    tracker.finish()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import wandb


class BaseTracker(ABC):
    """Abstract base class defining the experiment tracking interface."""
    
    @abstractmethod
    def __init__(self, run_name: str, config: dict[str, Any] | None = None, **kwargs: Any):
        pass

    @abstractmethod
    def add_metrics(self, step: int, **metrics: Any) -> None:
        """Log numerical values (e.g. loss, accuracy) over time."""
        pass

    @abstractmethod
    def add_config(self, **params: Any) -> None:
        """Add to the static configuration/hyperparameters for the run."""
        pass

    @abstractmethod
    def add_summary(self, **metrics: Any) -> None:
        """Log final summary metrics (e.g. best_val_acc)."""
        pass

    @abstractmethod
    def finish(self) -> None:
        """Clean up and close the tracker."""
        pass


class WBTracker(BaseTracker):
    """Tracks experiments using Weights & Biases."""
    
    def __init__(
        self,
        run_name: str,
        project: str = "ml-crucible",
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        self._run = wandb.init(
            project=project,
            name=run_name,
            config=config or {},
            **kwargs,
        )

    def add_metrics(self, step: int, **metrics: Any) -> None:
        if self._run is not None:
            self._run.log({"step": step, **metrics}, step=step)

    def add_config(self, **params: Any) -> None:
        if self._run is not None:
            self._run.config.update(params)

    def add_summary(self, **metrics: Any) -> None:
        if self._run is not None:
            for k, v in metrics.items():
                self._run.summary[k] = v

    def finish(self) -> None:
        """Explicitly finish the W&B run."""
        if self._run is not None:
            self._run.finish()
