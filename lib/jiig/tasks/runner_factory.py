"""
Default runner factory.

Is easily overridden by applications, because @runner_factory() registration
order follows task module loading order. So application @runner_factory()
decorator calls occur later and override the registration below.
"""
from jiig.runner import runner_factory, TaskRunner, RunnerData


@runner_factory()
def jiig_runner_factory(data: RunnerData) -> TaskRunner:
    return TaskRunner(data)
