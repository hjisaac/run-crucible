from abc import abstractmethod

from core.jobs.abstract import AbstractJob
from core.mixins.sgd import GradientDescentMixin


class AbstractTrainerJob(AbstractJob):
	"""Base class for all trainer jobs, regardless of optimization strategy."""

	def __init__(self, config) -> None:
		super().__init__(config)

	def setup(self) -> None:
		super().setup()
		self.setup_model()
		self.setup_metrics()
		self.setup_tracker()

	@abstractmethod
	def setup_model(self) -> None:
		pass

	@abstractmethod
	def setup_metrics(self) -> None:
		pass

	@abstractmethod
	def train(self) -> None:
		pass

	@abstractmethod
	def evaluate(self) -> None:
		pass

	def run(self):
		self.setup()
		return self.train()


class AbstractGDTrainerJob(AbstractTrainerJob, GradientDescentMixin):
	"""Trainer job that assumes gradient-descent-based optimization."""

	def setup(self) -> None:
		super().setup()
		self.setup_optimizer()
		self.setup_lr_scheduler()
