from abc import ABCMeta, abstractmethod
from datetime import datetime

from dotenv import load_dotenv

from crucible.core.handlers.logger import configure_logging

load_dotenv()


class AbstractJob(metaclass=ABCMeta):
	"""Base class for all executable jobs."""

	def __init__(self, config) -> None:
		self.config = config
		self._run_id = self._build_run_id()
		configure_logging(config, self._run_id)

	@staticmethod
	def _build_run_id() -> str:
		now = datetime.now()
		return f"{now.strftime('%Y-%b-%d_%H-%M-%S')}-{now.microsecond // 1000:03d}"

	@property
	def run_id(self) -> str:
		"""Unique identifier for a single run (execution) of this job, used for logging and tracking."""
		return self._run_id

	@abstractmethod
	def setup_data(self) -> None:
		pass

	def setup(self) -> None:
		self.setup_data()

	def setup_tracker(self) -> None:
		self.tracker = None

	@abstractmethod
	def run(self) -> None:
		pass
