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

"""
Pdoc3 HTML documentation generation task.
"""

import jiig
from jiig.util.text.pdoc import PdocBuilder


@jiig.task
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
                          runtime.meta.doc_api_packages_excluded,
                          runtime.paths.doc)
    if not builder.generate_html(force=force):
        runtime.abort('Failed to generate HTML format documentation.')
