"""
Runner provides data and an API to task call-back functions..
"""

from contextlib import contextmanager
from typing import Text, Iterator

from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog
from jiig.driver import Driver, DriverTask

from .runtime_context import RuntimeContext
from .runtime_task import RuntimeTask
from .runtime_tool import RuntimeTool


class Runtime(RuntimeContext):
    """Application runtime data and options."""

    def __init__(self,
                 tool: RuntimeTool,
                 root_task: RuntimeTask,
                 driver_root_task: DriverTask,
                 driver: Driver,
                 **kwargs,
                 ):
        """
        Construct root runtime context.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        :param tool: tool data
        :param root_task: active root task
        :param driver_root_task: active root task used by driver
        :param driver: active Jiig interface driver
        :param kwargs: initial symbols
        """
        self.tool = tool
        self.root_task = root_task
        self.driver_root_task = driver_root_task
        self.driver = driver
        super().__init__(None, **kwargs)

    @contextmanager
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with open_alias_catalog(self.tool.name, self.tool.aliases_path) as catalog:
            yield catalog

    def provide_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.driver.provide_help(self.driver_root_task, *names, show_hidden=show_hidden)
