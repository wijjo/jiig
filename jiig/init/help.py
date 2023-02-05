# Copyright (C) 2020-2023, Steven Cooper
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

"""Help generator initialization."""

from jiig.driver import Driver
from jiig.runtime import RuntimeHelpGenerator
from jiig.runtime_task import RuntimeTask


class HelpGenerator(RuntimeHelpGenerator):
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


def prepare_help_generator(*,
                           driver: Driver,
                           root_task: RuntimeTask,
                           ) -> HelpGenerator:
    """
    Prepare help generator.

    :param driver: active driver
    :param root_task: root runtime task
    :return: help generator
    """
    return HelpGenerator(driver, root_task)
