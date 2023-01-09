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

"""Tool specification."""

import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Self, Type, Callable

from jiig import constants
from jiig.driver import Driver, CLIDriver
from jiig.runtime import Runtime, RuntimeMetadata, RuntimePaths
from jiig.tool import Tool


@dataclass
class ToolConfiguration:
    """Tool configuration data."""
    options: Tool.Options
    meta: RuntimeMetadata
    paths: RuntimePaths
    runtime: Type[Runtime] | str | ModuleType
    driver: Type[Driver] | str | ModuleType
    driver_variant: str
    extra_symbols: dict[str, Any]
    venv_interpreter: str
    venv_active: bool
    venv_required: bool
    root_task: str | ModuleType | Callable | None

    @classmethod
    def prepare(cls, tool: Tool) -> Self:
        options = tool.Options or Tool.Options()

        if tool.tool_root_folder not in sys.path:
            sys.path.insert(0, tool.tool_root_folder)

        jiig_library_folder = _make_path(tool.jiig_library_folder, constants.JIIG_ROOT)

        library_folders: list[Path] = []
        if tool.library_folders is None:
            library_folders.append(jiig_library_folder)
        else:
            library_folders.extend(Path(folder) for folder in tool.library_folders)
        if jiig_library_folder not in library_folders:
            library_folders.append(jiig_library_folder)

        meta = RuntimeMetadata(
            tool_name=tool.tool_name,
            project_name=tool.project_name or tool.tool_name.capitalize(),
            author=tool.author or constants.DEFAULT_AUTHOR,
            copyright=tool.copyright or constants.DEFAULT_COPYRIGHT,
            description=tool.description or constants.DEFAULT_TOOL_DESCRIPTION,
            version=tool.version or '(unknown version)',
            top_task_label=tool.top_task_label or constants.TOP_TASK_LABEL,
            sub_task_label=tool.sub_task_label or constants.SUB_TASK_LABEL,
            pip_packages=tool.pip_packages or [],
            doc_api_packages=tool.doc_api_packages or [],
            doc_api_packages_excluded=tool.doc_api_packages_excluded or [],
        )

        paths = RuntimePaths(
            jiig_library=jiig_library_folder,
            jiig_root=_make_path(tool.jiig_root_folder, jiig_library_folder),
            tool_root=Path(tool.tool_root_folder),
            libraries=library_folders,
            venv=_make_path(tool.venv_folder, constants.JIIG_VENV_ROOT / tool.tool_name),
            aliases=_make_path(tool.aliases_path, constants.DEFAULT_ALIASES_PATH),
            build=_make_path(tool.build_folder, constants.DEFAULT_BUILD_FOLDER),
            doc=_make_path(tool.doc_folder, constants.DEFAULT_DOC_FOLDER),
            test=_make_path(tool.test_folder, constants.DEFAULT_TEST_FOLDER),
        )

        venv_interpreter = str(paths.venv / 'bin' / 'python')
        venv_active = sys.executable == venv_interpreter
        venv_required = meta.pip_packages or options.venv_required

        return cls(
            options=options,
            meta=meta,
            paths=paths,
            runtime=tool.runtime or Runtime,
            driver=tool.driver or CLIDriver,
            driver_variant=tool.driver_variant or constants.DEFAULT_DRIVER_VARIANT,
            extra_symbols=tool.extra_symbols or {},
            venv_interpreter=venv_interpreter,
            venv_active=venv_active,
            venv_required=venv_required,
            root_task=tool.root_task,
        )


def _make_path(raw_path: str | Path | None, default: Path) -> Path:
    if raw_path is None:
        return default
    if isinstance(raw_path, Path):
        return raw_path
    return Path(raw_path)
