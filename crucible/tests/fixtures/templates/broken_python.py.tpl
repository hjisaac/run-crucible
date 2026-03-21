from crucible.core.jobs import AbstractJob


class Job(AbstractJob)
	def setup_data(self) -> None:
		self.data = {{"status": "ready"}}

	def run(self) -> dict[str, str]:
		self.setup()
		return {{"status": "ok", "task": "{run_name}"}}


JOB_CLASS = Job
