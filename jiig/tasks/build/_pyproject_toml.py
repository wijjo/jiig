# Copyright (C) 2023, Steven Cooper
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
Generate pyproject.toml file.
"""

import jiig
from jiig.util.stream import open_output_file


PYPROJECT_TOML_TEMPLATE = '''\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "{version}"
authors = [
  {{ name="{author}", email="{email}" }},
]
description = "{description}"
readme = "README.md"
requires-python = ">=3.10"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Operating System :: OS Independent",
]

[project.urls]
"Homepage" = "{url}"
'''


def generate_pyproject_toml(runtime: jiig.Runtime):
    """
    Generate pyproject.toml for building distributions.

    :param runtime: runtime API, providing metadata and paths
    """
    toml_path = runtime.paths.tool_root / 'pyproject.toml'
    if toml_path.is_file():
        return
    runtime.message('Saving pyproject.toml...')
    toml_text = PYPROJECT_TOML_TEMPLATE.format(
        name=runtime.meta.tool_name,
        version=runtime.meta.version,
        author=runtime.meta.author,
        email=runtime.meta.email,
        description=runtime.meta.description,
        url=runtime.meta.url,
    )
    output_file = open_output_file(toml_path)
    output_file.write(toml_text)
