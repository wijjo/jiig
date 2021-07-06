"""Base driver class."""

from typing import Text, Sequence, List

from ..registry import SelfRegisteringDriverBase
from ..util.log import LogWriter

from .driver_task import DriverTask
from .driver_types import DriverApplicationData, DriverInitializationData
from .driver_options import DriverOptions

IMPLEMENTATION_CLASS_NAME = 'Implementation'


class Driver(SelfRegisteringDriverBase, skip_registration=True):
    """Jiig driver base class."""
    supported_hints: List[Text] = []

    def __init__(self,
                 name: Text,
                 description: Text,
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
        self.enabled_global_options: List[Text] = []
        self.phase = 'construction'

    def initialize_driver(self,
                          command_line_arguments: Sequence[Text],
                          ) -> DriverInitializationData:
        """
        Driver initialization.

        :param command_line_arguments: command line arguments
        :return: driver initialization data
        """
        self.phase = 'driver-initialization'
        return self.on_initialize_driver(command_line_arguments)

    def on_initialize_driver(self,
                             command_line_arguments: Sequence[Text],
                             ) -> DriverInitializationData:
        """
        Required driver initialization call-back.

        :param command_line_arguments: command line arguments
        :return: driver initialization data
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def provide_help(self,
                     root_task: DriverTask,
                     *names: Text,
                     show_hidden: bool = False):
        """
        Provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.on_provide_help(root_task, list(names), show_hidden)

    def on_provide_help(self,
                        root_task: DriverTask,
                        names: List[Text],
                        show_hidden: bool):
        """
        Required override to provide help output.

        :param root_task: root task
        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        raise NotImplementedError

    def get_log_writer(self) -> LogWriter:
        """
        Required override to provide a log writer.

        :return: log writer
        """
        raise NotImplementedError
