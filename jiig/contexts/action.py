"""
Context for text expansion and external command execution environment.
"""
import os
from typing import Optional

from .context import Context
from ._file_api import ActionContextFileAPI
from ._misc_api import ActionContextMiscAPI
from ._run_api import ActionContextRunAPI


class ActionContext(Context):
    """Nestable execution context with text expansion symbols."""

    def __init__(self, parent: Optional[Context], **kwargs):
        """
        Construct action context.

        :param parent: optional parent context for symbol inheritance
        :param kwargs: initial symbols
        """
        super().__init__(parent, **kwargs)
        self.initial_working_folder = os.getcwd()
        self.working_folder_changed = False
        # API namespaces
        self.run = ActionContextRunAPI(self)
        self.file = ActionContextFileAPI(self)
        self.misc = ActionContextMiscAPI(self)

    def __enter__(self) -> 'ActionContext':
        """
        Context management protocol enter method.

        Called at the start when an ActionContext is used in a with block. Saves
        the working directory.

        :return: Context object
        """
        self.initial_working_folder = os.getcwd()
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

    def working_folder(self, folder: str) -> str:
        """
        Change the working folder.

        Original working folder is restored by the contextmanager wrapped around
        the sub_context creation.

        :param folder: new working folder
        :return: previous working folder
        """
        os.chdir(folder)
        self.working_folder_changed = True
        return os.getcwd()
