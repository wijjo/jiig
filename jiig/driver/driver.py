# Copyright (C) 2021-2022, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Base driver class."""

from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Sequence

from ..runtime import RuntimePaths
from ..util.log import LogWriter

from .driver_task import DriverTask
from .driver_types import DriverApplicationData, DriverInitializationData
from .driver_options import DriverOptions

IMPLEMENTATION_CLASS_NAME = 'Implementation'


class Driver(ABC):
    """
    Jiig driver base class.

    Automatically registers concrete subclasses.
    """

    supported_task_hints: list[str] = []
    supported_field_hints: list[str] = []

    def __init__(self,
                 name: str,
                 description: str,
                 paths: RuntimePaths,
                 options: DriverOptions = None,
                 ):
        """
        Jiig driver constructor.

        :param name: tool name
        :param description: tool description
        :param paths: runtime paths
        :param options: various driver options
        """
        self.name = name
        self.description = description
        self.paths = paths
        self.options = options or DriverOptions()
        self.enabled_global_options: list[str] = []
        self.phase = 'construction'

    def __init_subclass__(cls, /, **kwargs):
        """Self-register Driver subclasses (only)."""
        super().__init_subclass__(**kwargs)
        if not isabstract(cls):
            # Import internal dependency locally so that this module could be
            # imported by the root package, if desired.
            from jiig.internal.registration.drivers import DRIVER_REGISTRY
            DRIVER_REGISTRY.register(cls)

    def initialize_driver(self,
                          command_line_arguments: Sequence[str],
                          ) -> DriverInitializationData:
        """
        Driver initialization.

        :param command_line_arguments: command line arguments
        :return: driver initialization data
        """
        self.phase = 'driver-initialization'
        return self.on_initialize_driver(command_line_arguments)

    @abstractmethod
    def on_initialize_driver(self,
                             command_line_arguments: Sequence[str],
                             ) -> DriverInitializationData:
        """
        Required driver initialization call-back.

        :param command_line_arguments: command line arguments
        :return: driver initialization data
        """
        ...

    def initialize_application(self,
                               initialization_data: DriverInitializationData,
                               root_task: DriverTask
                               ) -> DriverApplicationData:
        """
        Application initialization.

        :param initialization_data: application initialization data
        :param root_task: root task
        :return: driver application data
        """
        self.phase = 'application-initialization'
        return self.on_initialize_application(initialization_data, root_task)

    @abstractmethod
    def on_initialize_application(self,
                                  initialization_data: DriverInitializationData,
                                  root_task: DriverTask,
                                  ) -> DriverApplicationData:
        """
        Required application initialization call-back.

        :param initialization_data: driver initialization data
        :param root_task: root task
        :return: driver application data
        """
        ...

    def provide_help(self,
                     root_task: DriverTask,
                     *names: str,
                     show_hidden: bool = False):
        """
        Provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.on_provide_help(root_task, list(names), show_hidden)

    @abstractmethod
    def on_provide_help(self,
                        root_task: DriverTask,
                        names: list[str],
                        show_hidden: bool):
        """
        Required override to provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        ...

    @abstractmethod
    def get_log_writer(self) -> LogWriter:
        """
        Required override to provide a log writer.

        :return: log writer
        """
        ...
