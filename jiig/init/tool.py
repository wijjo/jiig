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

"""Tool configuration loading."""

from pathlib import Path
from typing import Any

from jiig.constants import (
    DEFAULT_ALIASES_PATH,
    DEFAULT_AUTHOR,
    DEFAULT_BUILD_FOLDER,
    DEFAULT_COPYRIGHT,
    DEFAULT_DOC_FOLDER,
    DEFAULT_EMAIL,
    DEFAULT_ROOT_TASK_NAME,
    DEFAULT_TEST_FOLDER,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    JIIG_JSON_CONFIGURATION_NAME,
    JIIG_TOML_CONFIGURATION_NAME,
    JIIG_VENV_ROOT,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
)
from jiig.task import TaskTree
from jiig.tool import (
    Tool,
    ToolCustomizations,
    ToolMetadata,
    ToolOptions,
    ToolPaths,
)
from jiig.types import ModuleReference
from jiig.util.collections import make_list
from jiig.util.configuration import (
    read_json_configuration,
    read_toml_configuration,
)
from jiig.util.filesystem import search_folder_stack_for_file
from jiig.util.python import find_package_base_folder
from jiig.util.log import abort, log_error


def _read_toml_configuration(config_path: Path,
                             ignore_decode_error: bool = False,
                             ) -> dict | None:
    try:
        return read_toml_configuration(config_path, ignore_decode_error=ignore_decode_error)
    except TypeError as type_exc:
        abort(str(type_exc))
    except ValueError as value_exc:
        abort(str(value_exc))
    except (IOError, OSError) as file_exc:
        abort(f'Failed to read TOML configuration file.',
              path=config_path,
              exception=file_exc)


def _read_json_configuration(config_path: Path,
                             ignore_decode_error: bool = False,
                             skip_file_header: bool = False,
                             ) -> dict | None:
    try:
        return read_json_configuration(config_path,
                                       skip_file_header=skip_file_header,
                                       ignore_decode_error=ignore_decode_error)
    except TypeError as type_exc:
        abort(str(type_exc))
    except ValueError as value_exc:
        abort(str(value_exc))
    except (IOError, OSError) as file_exc:
        abort(f'Failed to read JSON configuration file.',
              path=config_path,
              exception=file_exc)


def read_script_configuration(script_path: Path) -> dict:
    """
    Read TOML format configuration data from script or separate file.

    :param script_path: script path
    :return: configuration data
    """
    # First try parsing the script for TOML or JSON data.
    config_data = _read_toml_configuration(script_path,
                                           ignore_decode_error=True)
    if config_data is not None:
        return config_data
    config_data = _read_json_configuration(script_path,
                                           skip_file_header=True,
                                           ignore_decode_error=True)
    if config_data is not None:
        return config_data
    # Otherwise find and read a separate configuration file..
    config_path = search_folder_stack_for_file(script_path.parent,
                                               JIIG_TOML_CONFIGURATION_NAME)
    if config_path is not None:
        return _read_toml_configuration(config_path)
    config_path = search_folder_stack_for_file(script_path.parent,
                                               JIIG_JSON_CONFIGURATION_NAME)
    if config_path is not None:
        return _read_json_configuration(config_path)
    abort(f'Could not find {JIIG_TOML_CONFIGURATION_NAME} or'
          f' {JIIG_JSON_CONFIGURATION_NAME} based on script path.',
          script_path=script_path)


def load_tool_configuration(script_path: Path,
                            is_jiig: bool,
                            jiig_source_root: Path | None,
                            ) -> Tool:
    """
    Load tool.

    :param script_path: tool script path
    :param is_jiig: running Jiig tool if True
    :param jiig_source_root: optional Jiig source root folder
    :return: loaded Tool object
    """
    # TOML configuration data can either be embedded in the script or in a
    # separate file.
    config_data = read_script_configuration(script_path)
    extractor = _Extractor(config_data)

    options = ToolOptions(
        disable_alias=extractor.boolean('options.disable_alias', False),
        disable_help=extractor.boolean('options.disable_help', False),
        disable_debug=extractor.boolean('options.disable_debug', False),
        disable_dry_run=extractor.boolean('options.disable_dry_run', False),
        disable_verbose=extractor.boolean('options.disable_verbose', False),
        enable_pause=extractor.boolean('options.enable_pause', False),
        enable_keep_files=extractor.boolean('options.enable_keep_files', False),
        hide_builtin_tasks=extractor.boolean('options.hide_builtin_tasks', False),
        is_jiig=is_jiig,
    )

    custom = ToolCustomizations(
        runtime=extractor.any('tool.runtime', None),
        driver=extractor.any('tool.driver', None),
    )

    tool_name = extractor.string('tool.name', script_path.parent.name)
    project_name = extractor.string('tool.project', tool_name.capitalize())

    meta = ToolMetadata(
        tool_name=tool_name,
        project_name=project_name,
        author=extractor.string('tool.author', DEFAULT_AUTHOR),
        email=extractor.string('tool.email', DEFAULT_EMAIL),
        copyright=extractor.string('tool.copyright', DEFAULT_COPYRIGHT),
        description=extractor.string('tool.description', DEFAULT_TOOL_DESCRIPTION),
        url=extractor.string('tool.url', DEFAULT_URL),
        version=extractor.string('tool.version', DEFAULT_VERSION),
        top_task_label=extractor.string('tool.top_task_label', TOP_TASK_LABEL),
        sub_task_label=extractor.string('tool.top_task_label', SUB_TASK_LABEL),
        pip_packages=extractor.string_list('tool.pip_packages', []),
        doc_api_packages=extractor.string_list('tool.doc_api_packages', []),
        doc_api_packages_excluded=extractor.string_list('tool.doc_api_packages_excluded', []),
    )

    package = extractor.string('tool.tasks_package', None)
    task_tree = extractor.task_tree('tasks', DEFAULT_ROOT_TASK_NAME, package)

    # If a package is specified, use the configuration path as the basis for a
    # package folder search. The package parent folder will be added to the
    # Python library load path.
    tool_source_root: Path | None = None
    if package is not None and isinstance(package, str):
        tool_source_root = find_package_base_folder(package, script_path)
        if tool_source_root is None:
            log_error('Package folder not found:', package)

    venv_folder = JIIG_VENV_ROOT / tool_name
    paths = ToolPaths(
        libraries=extractor.path_list('tool.library_folders', []),
        venv=extractor.path('venv_folder', venv_folder),
        aliases=extractor.path('aliases_path', DEFAULT_ALIASES_PATH),
        build=extractor.path('build_folder', DEFAULT_BUILD_FOLDER),
        doc=extractor.path('doc_folder', DEFAULT_DOC_FOLDER),
        test=extractor.path('test_folder', DEFAULT_TEST_FOLDER),
        jiig_source_root=jiig_source_root,
        tool_source_root=tool_source_root,
    )

    return Tool(
        options=options,
        custom=custom,
        meta=meta,
        paths=paths,
        task_tree=task_tree,
        extra_symbols=extractor.dictionary('extra_symbols'),
    )


class _Extractor:
    def __init__(self, raw_data: dict):
        self.raw_data = raw_data

    def _get(self, name: str) -> Any | None:
        raw_data = self.raw_data
        name_parts = name.split('.')
        for name_part in name_parts[:-1]:
            if name_part not in raw_data:
                return None
            raw_data = raw_data[name_part]
            if not isinstance(raw_data, dict):
                return None
        return raw_data.get(name_parts[-1])

    def boolean(self, name: str, default: bool) -> bool:
        value = self._get(name)
        if value is None:
            return default
        if not isinstance(value, bool):
            log_error(f'Ignoring non-boolean "{name}" value: {value}')
            return default
        return value

    def string(self, name: str, default: str | None) -> str | None:
        value = self._get(name)
        if value is None:
            return default
        return str(value)

    def string_list(self, name: str, default: list[str]) -> list[str]:
        value = self._get(name)
        if value is None:
            return default
        return [str(s) for s in make_list(value)]

    def path(self, name: str, default: Path) -> Path:
        value = self._get(name)
        if value is None:
            return default
        if isinstance(value, Path):
            return value
        if not isinstance(value, str):
            return default
        return Path(value)

    def path_list(self, name: str, default: list[Path], *extra_paths: Path) -> list[Path]:
        value = self._get(name)
        if value is None:
            return default
        paths = [Path(item) for item in make_list(value)]
        for extra_path in extra_paths:
            if extra_path not in paths:
                paths.append(extra_path)
        return paths

    def task_tree(self, name: str, top_task_name: str, package: ModuleReference | None) -> TaskTree:
        value = self._get(name)
        if value is None:
            return TaskTree(name=top_task_name, sub_tasks=[])
        # The extracted value is just the sub-tasks. Wrap so that
        # TaskTree.from_raw_data() works properly.
        wrapped_data = {
            'package': package,
            'sub_tasks': value,
        }
        return TaskTree.from_raw_data(name=top_task_name, raw_data=wrapped_data)

    def any(self, name: str, default: Any) -> Any:
        value = self._get(name)
        if value is None:
            return default
        return value

    def dictionary(self, name: str) -> dict:
        value = self._get(name)
        if value is None or not isinstance(value, dict):
            return {}
        return value
