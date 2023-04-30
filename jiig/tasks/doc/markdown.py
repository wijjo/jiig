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

"""Pdoc3 PDF documentation generation task."""

import os
from dataclasses import dataclass
from pathlib import Path

import jiig
from jiig.util.filesystem import create_folder
from jiig.util.log import (
    abort,
    log_message,
)
from jiig.util.process import run
from jiig.util.stream import open_output_file


@jiig.task
def markdown(runtime: jiig.Runtime):
    """Use Pdoc3 to build Markdown-EXTRA format documentation.

    Args:
        runtime: Jiig runtime API.
    """
    generate_markdown(runtime)


@dataclass
class MarkdownResults:
    """Results of markdown generation."""
    #: Markdown file path.
    path: Path | None
    #: Pdoc command output.
    output: list[str]
    #: Pdoc command error output.
    error_output: list[str]


def generate_markdown(runtime: jiig.Runtime,
                      ) -> MarkdownResults:
    """Use Pdoc3 to generate Markdown-EXTRA format documentation.

    Args:
        runtime: Jiig runtime API.

    Returns:
        results data
    """

    output_path = Path(runtime.format_path('{doc_folder}', f'{runtime.meta.tool_name}.md'))
    pdoc_path = Path(runtime.format_path('{venv_folder}', 'bin', 'pdoc'))
    create_folder(output_path.parent, quiet=True)
    jiig_folder = Path(__file__).parent.parent.parent
    proc = run([pdoc_path, '--pdf', jiig_folder], capture=True)
    results = MarkdownResults(
        output_path if proc.returncode == 0 else None,
        proc.stdout.split(os.linesep),
        proc.stderr.split(os.linesep),
    )
    if results.path is not None:
        with open_output_file(output_path) as output_file:
            output_file.write(proc.stdout)
            log_message(f'Generated Markdown format documentation.', output_path)
            return results
    else:
        for line in results.error_output:
            log_message(line, tag='ERROR[PDOC]', is_error=True)
        for line in results.output:
            log_message(line, tag='[PDOC]')
        abort('Markdown generation failed.')
