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

"""
Context for text expansion and external command execution environment.
"""

import os
from pathlib import Path
from typing import Self

from jiig.util.options import OPTIONS

from jiig.context_api.file import ActionContextFileAPI
from jiig.context_api.misc import ActionContextMiscAPI
from jiig.context_api.run import ActionContextRunAPI

from .context import Context


class ActionContext(Context):
    """Nestable execution context with text expansion symbols."""

    def __init__(self, parent: Context | None, **kwargs):
        """
        Construct action context.

        :param parent: optional parent context for symbol inheritance
        :param kwargs: initial symbols
        """
        super().__init__(parent, **kwargs)
        self.initial_working_folder = Path(os.getcwd())
        self.working_folder_changed = False
        # API namespaces
        self.run = ActionContextRunAPI(self)
        self.file = ActionContextFileAPI(self)
        self.misc = ActionContextMiscAPI(self)
        # Convenient access to Jiig runtime options.
        self.options = OPTIONS

    def __enter__(self) -> Self:
        """
        Context management protocol enter method.

        Called at the start when an ActionContext is used in a with block. Saves
        the working directory.

        :return: Context object
        """
        self.initial_working_folder = Path(os.getcwd())
        self.working_folder_changed = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context management protocol exit method.

        Called at the end when an ActionContext is used in a with block.
        Restores the original working directory if it was changed by calling
        working_folder() method.

        :param exc_type: exception type
        :param exc_val: exception value
        :param exc_tb: exception traceback
        :return: True to suppress an exception that occurred in the with block
        """
        if self.working_folder_changed:
            os.chdir(self.initial_working_folder)
            self.working_folder_changed = False
        return False

    def working_folder(self, folder: str | Path) -> Path:
        """
        Change the working folder.

        Original working folder is restored by the contextmanager wrapped around
        the sub_context creation.

        :param folder: new working folder
        :return: previous working folder as pathlib.Path
        """
        os.chdir(folder)
        self.working_folder_changed = True
        return Path(os.getcwd())
