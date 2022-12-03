# Copyright (C) 2020-2022, Steven Cooper
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
Jiig utility library.
"""

# Provide package access to all modules that have no unwanted external
# dependencies. This allows clients to use fully-specified package names, e.g.
# jiig.util.general in code. The `gui` sub-package is an example of one that
# must be excluded due to its dependency on PySimpleGUI.
from . import (
    alias_catalog,
    log,
    date_time,
    filesystem,
    footnotes,
    general,
    help_formatter,
    init_file,
    json,
    network,
    options,
    process,
    python,
    repetition,
    scanners,
    stream,
    template_expansion,
)


from .options import OPTIONS
