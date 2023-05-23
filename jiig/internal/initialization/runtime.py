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

from jiig.constants import (
    DEFAULT_BUILD_FOLDER_NAME,
    DEFAULT_DOC_FOLDER_NAME,
    DEFAULT_TESTS_FOLDER_NAME,
    JIIG_CONFIG_ROOT,
    VENV_FOLDER_NAME,
)
from jiig.context import ActionContext
from jiig.driver import Driver
from jiig.runtime import Runtime
from jiig.task import RuntimeTask
from jiig.types import (
    ToolMetadata,
    ToolPaths,
)
from jiig.util.class_resolver import ClassResolver
from jiig.util.log import abort
from jiig.util.scoped_catalog import ScopedCatalog


def prepare_runtime(*,
                    runtime_spec: type[Runtime] | str | ModuleType | None,
                    meta: ToolMetadata,
                    venv_folder: str | Path | None,
                    base_folder: str | Path | None,
                    build_folder: str | Path | None,
                    doc_folder: str | Path | None,
                    test_folder: str | Path | None,
                    driver: Driver,
                    root_task: RuntimeTask,
                    aliases_catalog: ScopedCatalog,
                    params_catalog: ScopedCatalog,
                    ) -> Runtime:
    """Prepare runtime object passed to task functions.

    Args:
        runtime_spec: runtime class specification
        meta: tool metadata
        venv_folder: optional virtual environment override path
        base_folder: tool base folder containing tool package with task modules
        build_folder: optional build folder override
        doc_folder: optional documentation folder override
        test_folder: optional test folder override
        driver: driver
        root_task: runtime root task, e.g. for re-parsing command line for aliases
        aliases_catalog: aliases catalog instance
        params_catalog: parameters catalog instance

    Returns:
        prepared runtime object
    """
    # Get and check runtime class before creating an instance.
    if runtime_spec is None:
        runtime_spec = Runtime
    context_resolver = ClassResolver(ActionContext, 'runtime')
    runtime_registration = context_resolver.resolve_class(runtime_spec)
    runtime_class = runtime_registration.subclass
    assert issubclass(runtime_class, Runtime)
    if isinstance(base_folder, str):
        base_folder = Path(base_folder)
    paths = ToolPaths(
        venv=_resolve_path(venv_folder, JIIG_CONFIG_ROOT / meta.tool_name / VENV_FOLDER_NAME),
        base_folder=_resolve_path(base_folder),
        aliases_catalog_path=meta.aliases_catalog_path,
        params_catalog_path=meta.params_catalog_path,
        build=_resolve_path(build_folder, base_folder / DEFAULT_BUILD_FOLDER_NAME),
        doc=_resolve_path(doc_folder, base_folder / DEFAULT_DOC_FOLDER_NAME),
        test=_resolve_path(test_folder, base_folder / DEFAULT_TESTS_FOLDER_NAME),
    )
    try:
        return runtime_class(
            None,
            help_generator=driver.help_generator,
            data=driver.app_data.data,
            meta=meta,
            paths=paths,
            aliases_catalog=aliases_catalog,
            params_catalog=params_catalog,
            driver=driver,
            root_task=root_task,
        )
    except Exception as exc:
        abort(f'Exception while creating runtime class {runtime_class.__name__}',
              exc,
              exception_traceback_skip=1)


def _resolve_path(path: str | Path | None, default: Path = None) -> Path:
    if path is None:
        assert default is not None
        return default
    if isinstance(path, str):
        return Path(path).resolve()
    return path.resolve()
