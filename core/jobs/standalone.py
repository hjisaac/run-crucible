from core.jobs.abstract import AbstractJob


class AbstractStandaloneJob(AbstractJob):
	"""Semantic alias for non-training jobs."""

	pass


# Backward-compatible name used before the jobs split.
AbstractJob = AbstractStandaloneJob
