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

"""Library load path initialization."""

import sys
from pathlib import Path


def prepare_library_path(tool_source_root: Path | None,
                         jiig_library_paths: list[Path],
                         additional_library_paths: list[Path],
                         ):
    """Add necessary paths to Python library load path.

    Args:
        tool_source_root: tool source root, if known
        jiig_library_paths: jiig library paths
        additional_library_paths: additional library paths
    """
    # Add (missing) Jiig and tool library folders to Python library load path.
    for library_folder in jiig_library_paths:
        if library_folder not in sys.path:
            sys.path.insert(0, str(library_folder))
    if tool_source_root is not None and str(tool_source_root) not in sys.path:
        sys.path.insert(0, str(tool_source_root))
    for library_folder in additional_library_paths:
        if library_folder not in sys.path:
            sys.path.insert(0, str(library_folder))
