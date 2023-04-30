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

"""Pdoc3 documentation server task."""

import os
import jiig

from .html import generate_html


@jiig.task
def server(
    runtime: jiig.Runtime,
    port: jiig.f.integer() = 8080,
):
    """Use Pdoc3 to serve documentation using HTTP.

    Args:
        runtime: Jiig runtime API.
        port: HTTP server port (default: 8080).
    """
    html_folder = generate_html(runtime)
    os.chdir(html_folder)
    python = runtime.format_path('{venv_folder}', 'bin', 'python3')
    runtime.message(f'URL: http://localhost:{port}')
    os.execl(python, python, '-m', 'http.server', str(port))
