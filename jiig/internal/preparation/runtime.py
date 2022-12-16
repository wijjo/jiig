
from dataclasses import dataclass
from typing import Self

from jiig.driver import Driver, DriverTask
from jiig.runtime import Runtime, RuntimeHelpGenerator
from jiig.util.log import abort

from .application import PreparedApplication
from .driver import PreparedDriver
from jiig.internal.configuration.tool import ToolConfiguration


class HelpGenerator(RuntimeHelpGenerator):
    """Application help generator."""

    def __init__(self,
                 driver: Driver,
                 driver_root_task: DriverTask,
                 ):
        self.driver = driver
        self.driver_root_task = driver_root_task

    def generate_help(self, *names: str, show_hidden: bool = False):
        self.driver.provide_help(self.driver_root_task,
                                 *names,
                                 show_hidden=show_hidden)


@dataclass
class PreparedRuntime:
    runtime: Runtime

    @classmethod
    def prepare(cls,
                tool_config: ToolConfiguration,
                prepared_driver: PreparedDriver,
                prepared_application: PreparedApplication,
                ) -> Self:

        runtime_class = tool_config.runtime_registration.implementation
        assert issubclass(runtime_class, Runtime)
        try:
            runtime_instance = runtime_class(
                None,
                help_generator=HelpGenerator(prepared_driver.driver,
                                             prepared_application.driver_root_task),
                data=prepared_application.driver_app_data.data,
                meta=tool_config.meta,
                paths=tool_config.paths,
            )
            return cls(runtime_instance)
        except Exception as exc:
            abort(f'Exception while creating runtime class {runtime_class.__name__}',
                  exc,
                  exception_traceback_skip=1)
