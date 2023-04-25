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

"""Pdoc3 task utilities.

Since pdoc is a third party library, this module guards against import errors by
loading the library only as needed.
"""

import os
from pathlib import Path
from typing import Iterator

from ..filesystem import create_folder, short_path
from ..log import log_error, log_message
from ..stream import OutputRedirector

IGNORED_ERROR_TEXT = 'You are running a VERY old version of tkinter'


def _output_filter(line: str, is_error: bool = False) -> str | None:
    if is_error and line.find(IGNORED_ERROR_TEXT) != -1:
        return None
    return line


class PdocBuilder:
    """Utility class to build Pdoc documentation."""

    def __init__(self,
                 doc_api_packages: list[str],
                 doc_api_packages_excluded: list[str],
                 doc_folder: str | Path,
                 ):
        # Avoid pdoc dependency unless this class is used.
        import pdoc
        self.doc_api_packages = doc_api_packages
        self.doc_api_packages_excluded = doc_api_packages_excluded
        self.doc_folder = doc_folder if isinstance(doc_folder, Path) else Path(doc_folder)
        self.context = pdoc.Context()
        # Load pdoc modules and redirect/filter out unwanted Pdoc noise.
        with OutputRedirector(line_filter=_output_filter, auto_flush=True):
            # noinspection PyTypeChecker
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
            # noinspection PyTypeChecker
            yield from self._iterate_module(module)

    def generate_html(self, force: bool = False) -> bool:
        """Build HTML format documentation.

        Args:
            force: Overwrite existing files.

        Returns:
            True if HTML generation succeeded
        """
        if not force:
            for module in self.iterate_modules():
                path = os.path.join('html', *module.url().split('/')[1:])
                if os.path.exists(path):
                    if not os.path.isfile(path):
                        log_error(f'Output path exists, but is not a file.', path)
                        return False
                    log_error(f'One or more output files exist in the'
                              f' output folder "{self.doc_folder}".',
                              'Use -f or --force to overwrite.')
                    return False
        for module in self.iterate_modules():
            path = os.path.join(self.doc_folder,
                                *module.url().split('/')[1:])
            create_folder(os.path.dirname(path), quiet=True)
            try:
                log_message(short_path(path))
                with open(path, 'w', encoding='utf-8') as html_file:
                    html_file.write(module.html())
            except (IOError, OSError) as exc:
                log_error(f'Exception while writing HTML file.', path, exc)
                return False
        return True
