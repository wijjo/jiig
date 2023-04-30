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
from pathlib import Path

import jiig
from jiig.util.filesystem import find_system_program
from jiig.util.process import run
from jiig.util.stream import open_output_file

from .markdown import generate_markdown

CHROME_EXECUTABLES = ['chrome', 'chromium', 'thorium']


@jiig.task
def pdf(runtime: jiig.Runtime):
    """Use Pdoc3 to build PDF format documentation.

    Args:
        runtime: Jiig runtime API.
    """
    markdown_results = generate_markdown(runtime)
    md_path = Path(runtime.format_path('{doc_folder}', f'{runtime.meta.tool_name}.md'))
    html_path = Path(runtime.format_path('{doc_folder}', f'{runtime.meta.tool_name}-flat.html'))
    pdf_path = Path(runtime.format_path('{doc_folder}', f'{runtime.meta.tool_name}.pdf'))
    proc = run(
        [
            runtime.format_path('{venv_folder}', 'bin', 'markdown_py'),
            '--extension=abbr',
            '--extension=attr_list',
            '--extension=def_list',
            '--extension=fenced_code',
            '--extension=footnotes',
            '--extension=tables',
            '--extension=admonition',
            '--extension=smarty',
            '--extension=toc',
            md_path,
        ],
        unchecked=True,
        capture=True,
    )
    if runtime.options.verbose or proc.returncode != 0:
        for line in proc.stderr.split(os.linesep):
            runtime.message(line, tag='ERROR[MARKDOWN_PY]', is_error=True)
        for line in proc.stdout.split(os.linesep):
            runtime.message(line, tag='[MARKDOWN_PY]')
    if proc.returncode != 0:
        runtime.abort('Markdown to HTML conversion failed.')
    with open_output_file(html_path) as html_file:
        html_file.write(proc.stdout)
    pdoc_lines = [
        line
        for line in markdown_results.error_output
        if line.find('standard output') == -1 and line.find('^^^^^^^^^^^^^^^') == -1
    ]
    runtime.message('Generated flattened HTML for PDF.', html_path)
    chrome_cli: Path | None = None
    for executable_name in CHROME_EXECUTABLES:
        chrome_cli = find_system_program(executable_name)
    if chrome_cli is not None:
        proc = run(
            [
                chrome_cli.resolve(),
                '--headless',
                '--disable-gpu',
                f'--print-to-pdf={pdf_path}',
                html_path,
            ],
            unchecked=True,
            capture=True,
        )
        if proc.returncode == 0:
            runtime.message('Converted flattened HTML to PDF.', pdf_path)
        else:
            for line in proc.stderr.split(os.linesep):
                runtime.message(line, tag=f'ERROR[{chrome_cli.name}]', is_error=True)
            for line in proc.stdout.split(os.linesep):
                runtime.message(line, tag=f'[{chrome_cli.name}]')
    else:
        runtime.warning('Automatic conversion to final PDF is not available.')
        runtime.message(
            [
                'Chrome-based command line tools are supported, e.g. "chrome", "chromium",',
                'or "thorium", if they are in the system PATH.',
                'Otherwise, no simple/universal solution is available.',
                '',
                'See Pdoc suggestions below for ways to convert Markdown'
                ' or flattened HTML to a PDF:',
                '---',
            ] + pdoc_lines,
            html_path,
        )
