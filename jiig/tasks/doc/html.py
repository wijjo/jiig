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

"""Pdoc3 HTML documentation generation task."""

import os
from pathlib import Path

import jiig
from jiig.util.filesystem import create_folder
from jiig.util.process import run


@jiig.task
def html(runtime: jiig.Runtime):
    """Use Pdoc3 to build HTML format documentation.

    Args:
        runtime: Jiig runtime API.
    """
    generate_html(runtime)


def generate_html(runtime: jiig.Runtime) -> Path:
    """Use Pdoc3 to build HTML format documentation.

    Args:
        runtime: Jiig runtime API.

    Returns:
        HTML output folder path
    """
    doc_folder = Path(runtime.format('{doc_folder}'))
    html_folder = doc_folder / runtime.meta.tool_name
    create_folder(html_folder, delete_existing=True, quiet=True)
    proc = run(
        [
            runtime.format_path('{venv_folder}', 'bin', 'pdoc'),
            '--html',
            '-o', doc_folder,
            '--force',
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ],
        unchecked=True,
        capture=True,
    )
    if proc.returncode != 0:
        runtime.abort(
            [
                'HTML format documentation generation failed.',
            ] + proc.stderr.split(os.linesep),
        )
    runtime.message('Generated HTML format documentation folder.', html_folder)
    return html_folder
