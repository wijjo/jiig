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

from jiig.task import RuntimeTask
from jiig.types import RuntimeHelpGenerator
from jiig.util.log import LogWriter, log_message

from .driver_options import DriverOptions


@dataclass
class DriverPreliminaryAppData:
    """Preliminary application initialization data.

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
    """Jiig driver base class.

    Automatically registers concrete subclasses.
    """
    def __init__(self,
                 name: str,
                 description: str,
                 options: DriverOptions = None,
                 ):
        """Jiig driver constructor.

        Args:
            name: tool name
            description: tool description
            options: various driver options
        """
        self.name = name
        self.description = description
        self.options = options or DriverOptions()
        self.phase = 'construction'
        self.preliminary_app_data: DriverPreliminaryAppData | None = None
        self.app_data: DriverAppData | None = None
        self.help_generator: RuntimeHelpGenerator | None = None

    def initialize_driver(self,
                          command_line_arguments: Sequence[str],
                          ):
        """Driver initialization.

        Args:
            command_line_arguments: command line arguments
        """
        self.phase = 'driver-initialization'
        self.preliminary_app_data = self.on_initialize_driver(command_line_arguments)

    @abstractmethod
    def on_initialize_driver(self,
                             command_line_arguments: Sequence[str],
                             ) -> DriverPreliminaryAppData:
        """Required driver initialization call-back.

        Args:
            command_line_arguments: command line arguments

        Returns:
            preliminary app data
        """
        ...

    def initialize_application(self,
                               arguments: list[str],
                               root_task: RuntimeTask
                               ):
        """Driver application initialization.

        Args:
            arguments: argument list
            root_task: root task

        Returns:
            driver application data
        """
        self.phase = 'application-initialization'
        self.app_data = self.on_initialize_application(arguments, root_task)
        self.help_generator = DriverHelpGenerator(self, root_task)
        log_message('Application initialized.', debug=True)

    @abstractmethod
    def on_initialize_application(self,
                                  arguments: list[str],
                                  root_task: RuntimeTask,
                                  ) -> DriverAppData:
        """Required arguments initialization call-back.

        Args:
            arguments: argument list
            root_task: root task

        Returns:
            driver application data
        """
        ...

    def provide_help(self,
                     root_task: RuntimeTask,
                     *names: str,
                     show_hidden: bool = False):
        """Provide help output.

        Args:
            root_task: root task
            *names: name parts (task name stack)
            show_hidden: show hidden task help if True
        """
        self.on_provide_help(root_task, list(names), show_hidden)

    @abstractmethod
    def on_provide_help(self,
                        root_task: RuntimeTask,
                        names: list[str],
                        show_hidden: bool):
        """Required override to provide help output.

        Args:
            root_task: root task
            names: name parts (task name stack)
            show_hidden: show hidden task help if True
        """
        ...

    @abstractmethod
    def get_log_writer(self) -> LogWriter:
        """Required override to provide a log writer.

        Returns:
            log writer
        """
        ...


class DriverHelpGenerator(RuntimeHelpGenerator):
    """Application help generator."""

    def __init__(self,
                 driver: Driver,
                 root_task: RuntimeTask,
                 ):
        self.driver = driver
        self.root_task = root_task

    def generate_help(self, *names: str, show_hidden: bool = False):
        self.driver.provide_help(self.root_task,
                                 *names,
                                 show_hidden=show_hidden)
