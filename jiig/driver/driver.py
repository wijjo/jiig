# Copyright (C) 2021-2023, Steven Cooper
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
from dataclasses import dataclass
from typing import Sequence

from jiig.runtime_task import RuntimeTask
from jiig.util.log import LogWriter, log_message

from .driver_options import DriverOptions


@dataclass
class DriverPreliminaryAppData:
    """
    Preliminary application initialization data.

    E.g. for early access to global options.
    """
    # Attributes received from options.
    data: object
    # Additional arguments, not present as data attributes.
    additional_arguments: list[str]


@dataclass
class DriverAppData:
    """Data provided by driver application initialization."""
    # Attributes received from options and arguments.
    data: object
    # Command names.
    names: list[str]
    # Additional arguments, not present as data attributes.
    additional_arguments: list[str]
    # Task stack.
    task_stack: list[RuntimeTask]


class Driver(ABC):
    """
    Jiig driver base class.

    Automatically registers concrete subclasses.
    """
    def __init__(self,
                 name: str,
                 description: str,
                 options: DriverOptions = None,
                 ):
        """
        Jiig driver constructor.

        :param name: tool name
        :param description: tool description
        :param options: various driver options
        """
        self.name = name
        self.description = description
        self.options = options or DriverOptions()
        self.phase = 'construction'

    def initialize_driver(self,
                          command_line_arguments: Sequence[str],
                          ) -> DriverPreliminaryAppData:
        """
        Driver initialization.

        :param command_line_arguments: command line arguments
        :return: preliminary app data
        """
        self.phase = 'driver-initialization'
        return self.on_initialize_driver(command_line_arguments)

    @abstractmethod
    def on_initialize_driver(self,
                             command_line_arguments: Sequence[str],
                             ) -> DriverPreliminaryAppData:
        """
        Required driver initialization call-back.

        :param command_line_arguments: command line arguments
        :return: preliminary app data
        """
        ...

    def initialize_application(self,
                               arguments: list[str],
                               root_task: RuntimeTask
                               ) -> DriverAppData:
        """
        Driver application initialization.

        :param arguments: argument list
        :param root_task: root task
        :return: driver application data
        """
        self.phase = 'application-initialization'
        driver_app_data = self.on_initialize_application(arguments, root_task)
        log_message('Application initialized.', debug=True)
        return driver_app_data

    @abstractmethod
    def on_initialize_application(self,
                                  arguments: list[str],
                                  root_task: RuntimeTask,
                                  ) -> DriverAppData:
        """
        Required arguments initialization call-back.

        :param arguments: argument list
        :param root_task: root task
        :return: driver application data
        """
        ...

    def provide_help(self,
                     root_task: RuntimeTask,
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
                        root_task: RuntimeTask,
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
