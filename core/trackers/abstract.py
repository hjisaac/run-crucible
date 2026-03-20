from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractTracker(ABC):
    """Abstract base class defining the experiment tracking interface."""

    @abstractmethod
    def __init__(self, run_name: str, config: dict[str, Any] | None = None, **kwargs: Any):
        pass

    @abstractmethod
    def track_metrics(self, step: int, **metrics: Any) -> None:
        """Log numerical values (e.g. loss, accuracy) over time."""
        pass

    @abstractmethod
    def track_config(self, **params: Any) -> None:
        """Add to the static configuration/hyperparameters for the run."""
        pass

    @abstractmethod
    def track_summary(self, **metrics: Any) -> None:
        """Log final summary metrics (e.g. best_val_acc)."""
        pass

    @abstractmethod
    def finish(self) -> None:
        """Clean up and close the tracker."""
        pass
