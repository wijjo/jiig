"""ActionContext misc. API."""
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

from getpass import getpass
from typing import Sequence, Optional

from ..util.template_expansion import expand_folder

from .context import Context


class ActionContextMiscAPI:

    def __init__(self, context: Context):
        self.context = context

    def input_password(self, prompt: str = None) -> Optional[str]:
        """
        Input user password.

        :param prompt: optional prompt (default provided by getpass.getpass())
        :return: password
        """
        with self.context.context(prompt=prompt) as input_context:
            return getpass(prompt=input_context.s.prompt)

    def expand_template_folder(self,
                               source_root: str,
                               target_root: str,
                               sub_folder: str = None,
                               includes: Sequence[str] = None,
                               excludes: Sequence[str] = None,
                               overwrite: bool = False,
                               symbols: dict = None,
                               ):
        """
        Expand source template folder or sub-folder to target folder.

        Reads source template configuration, if found to determine what kind of
        special handling may be needed.

        :param source_root: template source root folder path
        :param target_root: base target folder
        :param sub_folder: optional relative sub-folder path applied to source and target roots
        :param includes: optional relative paths, supporting wildcards, for files to include
        :param excludes: optional relative paths, supporting wildcards, for files to exclude
        :param overwrite: force overwriting of existing files if True
        :param symbols: additional symbols used for template expansion
        """
        with self.context.context(source_root=source_root,
                                  target_root=target_root,
                                  sub_folder=sub_folder,
                                  includes=includes,
                                  excludes=excludes) as context:
            expand_folder(source_root,
                          target_root,
                          sub_folder=context.s.sub_folder,
                          includes=context.s.includes,
                          excludes=context.s.excludes,
                          overwrite=overwrite,
                          symbols=dict(self.context.s, **(symbols or {})),
                          )
