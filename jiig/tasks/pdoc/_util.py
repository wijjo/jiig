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
Pdoc3 task utilities.

Since pdoc is a third party library, this module guards against import errors by
loading the library only as needed.
"""

from typing import Text, List, Optional, Iterator

from jiig.util.stream import OutputRedirector

IGNORED_ERROR_TEXT = 'You are running a VERY old version of tkinter'


def _output_filter(line: Text, is_error: bool = False) -> Optional[Text]:
    if is_error and line.find(IGNORED_ERROR_TEXT) != -1:
        return None
    return line


class PdocBuilder:
    """Utility class to build Pdoc documentation."""

    def __init__(self,
                 doc_api_packages: List[Text],
                 doc_api_packages_excluded: List[Text],
                 ):
        import pdoc
        self.doc_api_packages = doc_api_packages
        self.doc_api_packages_excluded = doc_api_packages_excluded
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
