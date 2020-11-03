"""
Runner declaration support, including decorators.
"""

from typing import Callable

from jiig.internal.registry import register_runner_factory, RunnerFactoryFunction


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    """Decorator for custom runner factories."""
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        register_runner_factory(function)
        return function
    return inner
