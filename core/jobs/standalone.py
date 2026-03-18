from abc import ABCMeta, abstractmethod
from datetime import datetime
from dotenv import load_dotenv

from core.helpers.logger import configure_logging

load_dotenv()


class AbstractJob(metaclass=ABCMeta):
	"""Base class for all jobs (e.g. trainers, analysers)."""

	def __init__(self, config) -> None:
		self.config = config
		self._job_id = self._build_job_id()
		configure_logging(config, self._job_id)

	@staticmethod
	def _build_job_id() -> str:
		now = datetime.now()
		return f"{now.strftime('%Y-%b-%d_%H-%M-%S')}-{now.microsecond // 1000:03d}"

	@property
	def job_id(self) -> str:
		"""Unique identifier for this run, used for logging and tracking."""
		return self._job_id

	@abstractmethod
	def setup_data(self) -> None:
		pass

	def setup(self) -> None:
		# Inputs setup happens here.
		self.setup_data()

	def setup_tracker(self) -> None:
		self.tracker = None

	@abstractmethod
	def run(self) -> None:
		pass
