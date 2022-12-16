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

"""Tool creation task."""

import os

import jiig
from jiig.util.template_expansion import expand_folder


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
            'tool_name': ('-T', '--tool-name'),
        }
    }
)
def script(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
    tool_name: jiig.f.text(),
    tool_folder: jiig.f.filesystem_folder(absolute_path=True) = '.',
):
    """

    Create monolithic Jiig tool script.

    :param runtime: Jiig runtime API.
    :param force: Force overwriting of target files.
    :param tool_name: Tool name (default: working folder name).
    :param tool_folder: Generated tool output folder.
    """
    expand_folder(
        os.path.join(runtime.paths.jiig_root, 'templates/tool/script'),
        tool_folder,
        overwrite=force,
        symbols={
            'jiig_root': runtime.paths.jiig_root,
            'mytool': tool_name or os.path.basename(tool_folder),
        },
    )
