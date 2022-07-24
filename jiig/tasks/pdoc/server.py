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
Pdoc3 documentation server task.
"""

import jiig


# noinspection PyUnusedLocal
@jiig.task(
    cli={
        'options': {
            'port': ('-p', '--port'),
        },
    },
)
def server(
    runtime: jiig.Runtime,
    port: jiig.f.integer(),
):
    """
    Use Pdoc3 to serve documentation using HTTP.

    :param runtime: Jiig runtime API.
    :param port: HTTP server port (default: 8080).
    """
    raise NotImplementedError
