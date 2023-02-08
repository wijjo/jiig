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
    DEFAULT_TEST_FOLDER,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    HOME_FOLDER_PATH,
    JIIG_CONFIGURATION_NAME,
    JIIG_VENV_ROOT,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
)
from jiig.runtime import RuntimeMetadata, RuntimePaths
from jiig.task import TaskTree
from jiig.tool import Tool, ToolOptions, ToolCustomizations
from jiig.util.collections import make_list
from jiig.util.log import abort, log_error


def _read_config_file(config_path: Path) -> dict:
    try:
        import yaml
        with open(config_path, encoding='utf-8') as config_file:
            try:
                config_data = yaml.safe_load(config_file)
                if not isinstance(config_data, dict):
                    abort(f'Configuration file data is not a dictionary.',
                          path=config_path)
                return config_data
            except yaml.YAMLError as yaml_exc:
                abort(f'Unable to parse configuration file.',
                      path=config_path,
                      exception=yaml_exc)
    except (IOError, OSError) as file_exc:
        abort(f'Failed to read configuration file.',
              path=config_path,
              exception=file_exc)


class _Extractor:
    def __init__(self, raw_data: dict):
        self.raw_data = raw_data
        self.extracted_names: set[str] = set()

    def boolean(self, name: str, default: bool) -> bool:
        self.extracted_names.add(name)
        value = self.raw_data.get(name, default)
        if not isinstance(value, bool):
            log_error(f'Ignoring non-boolean "{name}" value: {value}')
            value = default
        return value

    def string(self, name: str, default: str | None) -> str | None:
        self.extracted_names.add(name)
        return str(self.raw_data.get(name, default))

    def string_list(self, name: str, default: list[str]) -> list[str]:
        self.extracted_names.add(name)
        return [str(s) for s in make_list(self.raw_data.get(name, default))]

    def path(self, name: str, default: Path) -> Path:
        self.extracted_names.add(name)
        raw_path = self.raw_data.get(name, default)
        if isinstance(raw_path, Path):
            return raw_path
        return Path(raw_path)

    def path_list(self, name: str, default: list[Path], *extra_paths: Path) -> list[Path]:
        self.extracted_names.add(name)
        if name not in self.raw_data:
            return default
        paths = [Path(item) for item in make_list(self.raw_data.get(name))]
        for extra_path in extra_paths:
            if extra_path not in paths:
                paths.append(extra_path)
        return paths

    def task_tree(self, name: str, top_task_name: str) -> TaskTree:
        self.extracted_names.add(name)
        raw_tasks = self.raw_data.get(name, {})
        return TaskTree.from_raw_data(name=top_task_name, raw_data=raw_tasks)

    def any(self, name: str, default: Any) -> Any:
        self.extracted_names.add(name)
        return self.raw_data.get(name, default)

    def extra_symbols(self) -> dict:
        return {
            name: self.raw_data[name]
            for name in set(self.raw_data.keys()).difference(self.extracted_names)
        }


def load_tool(tool_root: Path,
              jiig_root: Path,
              ) -> Tool:
    """
    Load tool.

    :param tool_root: tool root folder
    :param jiig_root: jiig root folder
    :return: loaded Tool object
    """
    config_path = tool_root / JIIG_CONFIGURATION_NAME
    config_data = _read_config_file(config_path)
    extractor = _Extractor(config_data)

    options = ToolOptions(
        disable_alias=extractor.boolean('disable_alias', False),
        disable_help=extractor.boolean('disable_help', False),
        disable_debug=extractor.boolean('disable_debug', False),
        disable_dry_run=extractor.boolean('disable_dry_run', False),
        disable_verbose=extractor.boolean('disable_verbose', False),
        enable_pause=extractor.boolean('enable_pause', False),
        enable_keep_files=extractor.boolean('enable_keep_files', False),
        hide_builtin_tasks=extractor.boolean('hide_builtin_tasks', False),
        venv_required=extractor.boolean('venv_required', False),
    )

    tool_name = extractor.string('tool_name', tool_root.name)
    project_name = extractor.string('project_name', tool_name.capitalize())

    meta = RuntimeMetadata(
        tool_name=tool_name,
        project_name=project_name,
        author=extractor.string('author', DEFAULT_AUTHOR),
        email=extractor.string('email', DEFAULT_EMAIL),
        copyright=extractor.string('copyright', DEFAULT_COPYRIGHT),
        description=extractor.string('description', DEFAULT_TOOL_DESCRIPTION),
        url=extractor.string('url', DEFAULT_URL),
        version=extractor.string('version', DEFAULT_VERSION),
        top_task_label=extractor.string('top_task_label', TOP_TASK_LABEL),
        sub_task_label=extractor.string('top_task_label', SUB_TASK_LABEL),
        pip_packages=extractor.string_list('pip_packages', []),
        doc_api_packages=extractor.string_list('doc_api_packages', []),
        doc_api_packages_excluded=extractor.string_list('doc_api_packages_excluded', []),
    )

    venv_folder = JIIG_VENV_ROOT / tool_root.relative_to(HOME_FOLDER_PATH)
    paths = RuntimePaths(
        jiig_root=jiig_root,
        tool_root=tool_root,
        libraries=extractor.path_list('library_folders', [], jiig_root, tool_root),
        venv=extractor.path('venv_folder', venv_folder),
        aliases=extractor.path('aliases_path', DEFAULT_ALIASES_PATH),
        build=extractor.path('build_folder', DEFAULT_BUILD_FOLDER),
        doc=extractor.path('doc_folder', DEFAULT_DOC_FOLDER),
        test=extractor.path('test_folder', DEFAULT_TEST_FOLDER),
    )

    task_tree = extractor.task_tree('tasks', '(root)')

    custom = ToolCustomizations(
        runtime=extractor.any('runtime', None),
        driver=extractor.any('driver', None),
    )

    return Tool(
        options=options,
        custom=custom,
        meta=meta,
        paths=paths,
        task_tree=task_tree,
        extra_symbols=extractor.extra_symbols(),
    )
