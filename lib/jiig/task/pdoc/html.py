"""
Pdoc3 HTML documentation generation task.
"""

import os

import jiig
from jiig.util.console import abort, log_message
from jiig.util.filesystem import create_folder, short_path

from ._util import PdocBuilder


def _module_path(module):
    return os.path.join('html', *module.url().split('/')[1:])


TASK = jiig.Task(
    description='Use Pdoc3 to build HTML format documentation.',
    args={
        'FORCE[!]': ('-f', '--force', 'overwrite existing files'),
    },
)


class Data:
    FORCE: bool


@TASK.run
def task_run(runner: jiig.Runner, data: Data):
    builder = PdocBuilder(runner.tool.doc_api_packages,
                          runner.tool.doc_api_packages_excluded)
    if not data.FORCE:
        for module in builder.iterate_modules():
            path = _module_path(module)
            if os.path.exists(path):
                if not os.path.isfile(path):
                    abort(f'Output path exists, but is not a file.', path)
                abort(f'One or more output files exist in the'
                      f' output folder "{runner.tool.doc_folder}".',
                      'Use -f or --force to overwrite.')
    for module in builder.iterate_modules():
        path = os.path.join(runner.tool.doc_folder,
                            *module.url().split('/')[1:])
        create_folder(os.path.dirname(path), quiet=True)
        try:
            log_message(short_path(path))
            with open(path, 'w', encoding='utf-8') as html_file:
                html_file.write(module.html())
        except (IOError, OSError) as exc:
            abort(f'Failed to write HTML file.', path, exc)
