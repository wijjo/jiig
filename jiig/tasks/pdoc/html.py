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
Pdoc3 HTML documentation generation task.
"""

import os

import jiig
from jiig.util.filesystem import create_folder, short_path

from ._util import PdocBuilder


def _module_path(module):
    return os.path.join('html', *module.url().split('/')[1:])


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
        },
    },
)
def html(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
):
    """
    Use Pdoc3 to build HTML format documentation.

    :param runtime: Jiig runtime API.
    :param force: Overwrite existing files.
    """
    builder = PdocBuilder(runtime.meta.doc_api_packages,
                          runtime.meta.doc_api_packages_excluded)
    if not force:
        for module in builder.iterate_modules():
            path = _module_path(module)
            if os.path.exists(path):
                if not os.path.isfile(path):
                    runtime.abort(f'Output path exists, but is not a file.', path)
                runtime.abort(f'One or more output files exist in the'
                              f' output folder "{runtime.paths.doc}".',
                              'Use -f or --force to overwrite.')
    for module in builder.iterate_modules():
        path = os.path.join(runtime.paths.doc,
                            *module.url().split('/')[1:])
        create_folder(os.path.dirname(path), quiet=True)
        try:
            runtime.message(short_path(path))
            with open(path, 'w', encoding='utf-8') as html_file:
                html_file.write(module.html())
        except (IOError, OSError) as exc:
            runtime.abort(f'Failed to write HTML file.', path, exc)
