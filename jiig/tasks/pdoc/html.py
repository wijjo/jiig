"""
Pdoc3 HTML documentation generation task.
"""

import os

import jiig
from jiig.util.filesystem import create_folder, short_path

from ._util import PdocBuilder


def _module_path(module):
    return os.path.join('html', *module.url().split('/')[1:])


class Task(jiig.Task):
    """Use Pdoc3 to build HTML format documentation."""

    force: jiig.f.boolean('Overwrite existing files.', cli_flags=('-f', '--force'))

    def on_run(self, runtime: jiig.Runtime):
        builder = PdocBuilder(runtime.tool.doc_api_packages,
                              runtime.tool.doc_api_packages_excluded)
        if not self.force:
            for module in builder.iterate_modules():
                path = _module_path(module)
                if os.path.exists(path):
                    if not os.path.isfile(path):
                        runtime.abort(f'Output path exists, but is not a file.', path)
                    runtime.abort(f'One or more output files exist in the'
                                  f' output folder "{runtime.tool.doc_folder}".',
                                  'Use -f or --force to overwrite.')
        for module in builder.iterate_modules():
            path = os.path.join(runtime.tool.doc_folder,
                                *module.url().split('/')[1:])
            create_folder(os.path.dirname(path), quiet=True)
            try:
                runtime.message(short_path(path))
                with open(path, 'w', encoding='utf-8') as html_file:
                    html_file.write(module.html())
            except (IOError, OSError) as exc:
                runtime.abort(f'Failed to write HTML file.', path, exc)
