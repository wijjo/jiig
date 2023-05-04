# Copyright (C) 2020-2023, Steven Cooper
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

"""Runtime object initialization."""

from pathlib import Path
from types import ModuleType
from typing import Type

from jiig.constants import (
    ALIASES_FOLDER_PATH,
    DEFAULT_BUILD_FOLDER,
    DEFAULT_DOC_FOLDER,
    DEFAULT_TEST_FOLDER,
    JIIG_VENV_ROOT,
)
from jiig.context import ActionContext
from jiig.driver import Driver
from jiig.runtime import Runtime
from jiig.task import RuntimeTask
from jiig.tool import ToolMetadata, ToolPaths
from jiig.util.alias_catalog import (
    is_alias_name,
    open_alias_catalog,
)
from jiig.util.class_resolver import ClassResolver
from jiig.util.log import abort


def prepare_runtime(*,
                    runtime_spec: Type[Runtime] | str | ModuleType | None,
                    runtime_root_task: RuntimeTask,
                    meta: ToolMetadata,
                    venv_folder: str | Path | None,
                    base_folder: str | Path | None,
                    build_folder: str | Path | None,
                    doc_folder: str | Path | None,
                    test_folder: str | Path | None,
                    driver: Driver,
                    extra_symbols: dict,
                    ) -> Runtime:
    """Prepare runtime object passed to task functions.

    Args:
        runtime_spec: runtime class specification
        runtime_root_task: runtime task tree root
        meta: tool metadata
        venv_folder: optional virtual environment override path
        base_folder: tool base folder containing tool package with task modules
        build_folder: optional build folder override
        doc_folder: optional documentation folder override
        test_folder: optional test folder override
        driver: driver
        extra_symbols: extra application symbols in Runtime object

    Returns:
        prepared runtime object
    """
    # Get and check runtime class.
    if runtime_spec is None:
        runtime_spec = Runtime
    context_resolver = ClassResolver(ActionContext, 'runtime')
    runtime_registration = context_resolver.resolve_class(runtime_spec)
    runtime_class = runtime_registration.subclass
    assert issubclass(runtime_class, Runtime)

    paths = ToolPaths(
        venv=_resolve_path(venv_folder, JIIG_VENV_ROOT / meta.tool_name),
        base_folder=_resolve_path(base_folder),
        aliases_path=ALIASES_FOLDER_PATH / f'{meta.tool_name}.json',
        build=_resolve_path(build_folder, DEFAULT_BUILD_FOLDER),
        doc=_resolve_path(doc_folder, DEFAULT_DOC_FOLDER),
        test=_resolve_path(test_folder, DEFAULT_TEST_FOLDER),
    )

    # Expand alias as needed and provide 'help' as default command.
    expanded_arguments = _expand_alias(
        driver.preliminary_app_data.additional_arguments,
        paths.aliases_path,
    )
    if not expanded_arguments:
        expanded_arguments = ['help']

    # Initialize driver to access app data object and help generator.
    driver.initialize_application(
        arguments=expanded_arguments,
        root_task=runtime_root_task,
    )

    try:
        runtime_instance = runtime_class(
            None,
            help_generator=driver.help_generator,
            data=driver.app_data.data,
            meta=meta,
            paths=paths,
            **extra_symbols,
        )
        return runtime_instance
    except Exception as exc:
        abort(f'Exception while creating runtime class {runtime_class.__name__}',
              exc,
              exception_traceback_skip=1)


def _expand_alias(arguments: list[str],
                  aliases_path: Path,
                  ) -> list[str]:
    expanded_arguments: list[str] = []
    if arguments:
        if not is_alias_name(arguments[0]):
            expanded_arguments.extend(arguments)
        else:
            with open_alias_catalog(aliases_path) as alias_catalog:
                alias = alias_catalog.get_alias(arguments[0])
                if not alias:
                    abort(f'Alias "{arguments[0]}" not found.')
                expanded_arguments = alias.command + arguments[1:]
    return expanded_arguments


def _resolve_path(path: str | Path | None, default: Path = None) -> Path:
    if path is None:
        assert default is not None
        return default
    if isinstance(path, str):
        return Path(path).resolve()
    return path.resolve()
