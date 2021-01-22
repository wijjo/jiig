"""
Use Pdoc3 for documentation generation.
"""

import os
import pdoc
from typing import Iterator, Text, Optional, List

from jiig import model
from jiig.util.console import abort, log_message
from jiig.util.filesystem import create_folder, short_path
from jiig.util.stream import OutputRedirector

IGNORED_ERROR_TEXT = 'You are running a VERY old version of tkinter'


def _module_path(module):
    return os.path.join('html', *module.url().split('/')[1:])


def _output_filter(line: Text, is_error: bool = False) -> Optional[Text]:
    if is_error and line.find(IGNORED_ERROR_TEXT) != -1:
        return None
    return line


class _PdocBuilder:

    def __init__(self,
                 doc_api_packages: List[Text],
                 doc_api_packages_excluded: List[Text],
                 ):
        self.doc_api_packages = doc_api_packages
        self.doc_api_packages_excluded = doc_api_packages_excluded
        self.context = pdoc.Context()
        # Load pdoc modules and redirect/filter out unwanted Pdoc noise.
        with OutputRedirector(line_filter=_output_filter, auto_flush=True):
            self.modules = [
                pdoc.Module(package_name,
                            context=self.context,
                            skip_errors=True,
                            docfilter=self._is_documented)
                for package_name in doc_api_packages
            ]
            pdoc.link_inheritance(self.context)

    def _is_documented(self, module) -> bool:
        name_parts = module.name.split('.')
        for part_idx in range(len(name_parts)):
            name = '.'.join(name_parts[:len(name_parts) - part_idx])
            if name in self.doc_api_packages_excluded:
                return False
        return True

    def _iterate_module(self, module) -> Iterator:
        if self._is_documented(module):
            yield module
            for iter_submodule in module.submodules():
                for submodule in self._iterate_module(iter_submodule):
                    if self._is_documented(submodule):
                        yield submodule

    def iterate_modules(self) -> Iterator:
        for module in self.modules:
            yield from self._iterate_module(module)


class PdocHTMLTask(model.Task):
    """Use Pdoc3 to build HTML format documentation."""

    class Data:
        FORCE: bool
    data: Data

    args = {
        'FORCE!': ('-f', '--force', 'overwrite existing files'),
    }

    def on_run(self):
        builder = _PdocBuilder(self.configuration.doc_api_packages,
                               self.configuration.doc_api_packages_excluded)
        if not self.data.FORCE:
            for module in builder.iterate_modules():
                path = _module_path(module)
                if os.path.exists(path):
                    if not os.path.isfile(path):
                        abort(f'Output path exists, but is not a file.', path)
                    abort(f'One or more output files exist in the'
                          f' output folder "{self.configuration.doc_folder}".',
                          'Use -f or --force to overwrite.')
        for module in builder.iterate_modules():
            path = os.path.join(self.configuration.doc_folder,
                                *module.url().split('/')[1:])
            create_folder(os.path.dirname(path), quiet=True)
            try:
                log_message(short_path(path))
                with open(path, 'w', encoding='utf-8') as html_file:
                    html_file.write(module.html())
            except (IOError, OSError) as exc:
                abort(f'Failed to write HTML file.', path, exc)


class PdocPDFTask(model.Task):
    """Use Pdoc3 to build PDF format documentation."""
    def on_run(self):
        pass


class PdocServerTask(model.Task):
    """Use Pdoc3 to serve documentation using HTTP."""

    # For type inspection assistance only.
    class Data:
        PORT: int
    data: Data

    args = {
        'PORT': ('-p', '--port', 'HTTP server port (default: 8080)', int),
    }

    def on_run(self):
        pass


class TaskClass(model.Task):
    """Pdoc3 documentation tasks."""

    options = model.TaskOptions(
        pip_packages=[
            'pdoc3',
            # PySimpleGUI is needed by admin_panel, which is being loaded by pdoc.
            'PySimpleGUI',
        ],
    )

    sub_tasks = {
        'html': PdocHTMLTask,
        'pdf': PdocPDFTask,
        'server': PdocServerTask,
    }

    def on_run(self):
        pass
