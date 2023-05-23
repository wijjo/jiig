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

"""Startup main functions.

tool_main(): Called by pure Python tools with pre-populated Tool data.

jiig_run(): Called by scripts using `jiig_run` as the "shebang" line
interpreter. Tool data is populated based on configuration information embedded
in the tool script.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

from .constants import (
    DEFAULT_AUTHOR,
    DEFAULT_COPYRIGHT,
    DEFAULT_EMAIL,
    DEFAULT_ROOT_TASK_NAME,
    DEFAULT_TOOL_DESCRIPTION,
    DEFAULT_URL,
    DEFAULT_VERSION,
    JIIG_CONFIG_ROOT,
    JIIG_JSON_CONFIGURATION_NAME,
    JIIG_TOML_CONFIGURATION_NAME,
    SUB_TASK_LABEL,
    TOP_TASK_LABEL,
    VENV_FOLDER_NAME,
)
from .task import TaskTree
from .types import (
    ToolCustomizations,
    ToolMetadata,
    ToolOptions,
)
from .util.collections import (
    AttributeDictionary,
    make_list,
)
from .util.configuration import (
    read_json_configuration,
    read_toml_configuration,
)
from .util.filesystem import search_folder_stack_for_file
from .util.log import (
    abort,
    log_error,
)
from .util.stream import open_input_file

RE_CONFIG_EMPTY_LINE = re.compile(r'^\s*$')
RE_CONFIG_COMMENT_LINE = re.compile(r'^\s*#.*\s*$')
RE_CONFIG_FIRST_LINE = re.compile(r'\s*(\[\w+\]|\{)\s*$')


def _fatal(*messages: str):
    for message in messages:
        sys.stderr.write(f'FATAL: {message}{os.linesep}')
    sys.stderr.write(os.linesep)
    sys.exit(1)


def _read_toml_configuration(config_path: Path,
                             ignore_decode_error: bool = False,
                             ) -> AttributeDictionary | None:
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
                             ) -> AttributeDictionary | None:
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


def _read_script_configuration(script_path: Path) -> AttributeDictionary:
    # The first character of the first non-comment/non-blank line can help
    # indentify the configuration format.
    config_format: str | None = None
    with open_input_file(script_path) as script_file:
        for line in script_file:
            if not RE_CONFIG_COMMENT_LINE.match(line) and not RE_CONFIG_EMPTY_LINE.match(line):
                match_first_line = RE_CONFIG_FIRST_LINE.match(line)
                if match_first_line is not None:
                    first_chunk = match_first_line.group(1)
                    if first_chunk.startswith('['):
                        config_format = 'toml'
                    elif first_chunk.startswith('{'):
                        config_format = 'json'

    if config_format == 'toml':
        return _read_toml_configuration(script_path)
    if config_format == 'json':
        return _read_json_configuration(script_path, skip_file_header=True)
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


class _ConfigurationDataExtractor:

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

    def path(self, name: str) -> Path | None:
        value = self._get(name)
        if value is None:
            return None
        if isinstance(value, Path):
            return value
        if not isinstance(value, str):
            return None
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

    def task_tree(self, name: str, top_task_name: str) -> TaskTree:
        value = self._get(name)
        if value is None:
            return TaskTree(name=top_task_name, sub_tasks=[])
        # The extracted value is just the sub-tasks. Wrap so that
        # TaskTree.from_raw_data() works properly.
        wrapped_data = {'sub_tasks': value}
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

    def params(self, name: str) -> tuple[dict[str, Any], dict[str, str]]:
        raw_params = self.dictionary(name)
        values: dict[str, Any] = {}
        comments: dict[str, str] = {}
        for name, param_data in raw_params.items():
            if 'value' in param_data:
                values[name] = param_data['value']
                comments[name] = param_data.get('comment', '(no comment)')
            else:
                log_error('Ignoring configured default with no "value".')
        return values, comments


def tool_main(meta: ToolMetadata,
              task_tree: TaskTree,
              script_path: str | Path,
              venv_folder: str | Path = None,
              build_folder: str | Path = None,
              doc_folder: str | Path = None,
              test_folder: str | Path = None,
              runner_args: list[str] = None,
              cli_args: list[str] = None,
              options: ToolOptions = None,
              custom: ToolCustomizations = None,
              param_defaults: dict[str, Any] = None,
              param_comments: dict[str, str] = None,
              skip_venv_preparation: bool = False,
              ):
    """Start a Jiig tool application based on Python tool data objects.

    This function is used by pure Python tools that can provide all the tool and
    task data.

    Args:
        meta: tool metadata
        task_tree: task tree
        script_path: tool script path
        venv_folder: optional virtual environment override path
        build_folder: optional build folder override
        doc_folder: optional documentation folder override
        test_folder: optional test folder override
        runner_args: runner argument list (default: sys.argv[:1])
        cli_args: CLI argument list (default: sys.argv[1:])
        options: tool options
        custom: optional tool customizations
        param_defaults: optional tool parameter defaults
        param_comments: optional tool parameter comments
        skip_venv_preparation: skip active virtual environment preparation if True
    """
    from .internal import execution, initialization

    # Provide defaults for missing parameters.
    if options is None:
        options = ToolOptions()
    if custom is None:
        custom = ToolCustomizations(None, None)
    if runner_args is None:
        runner_args = sys.argv[:1]
    if cli_args is None:
        cli_args = sys.argv[1:]

    # Check, prepare, and invoke virtual environment as needed.
    if venv_folder is None:
        venv_folder = JIIG_CONFIG_ROOT / meta.tool_name / VENV_FOLDER_NAME
    if not skip_venv_preparation:
        initialization.prepare_virtual_environment(
            venv_folder=venv_folder,
            runner_args=runner_args,
            cli_args=cli_args,
            packages=meta.pip_packages,
        )

    # Load driver.
    driver = initialization.prepare_driver(
        driver_spec=custom.driver,
        args=cli_args,
        tool_name=meta.tool_name,
        options=options,
        description=meta.description,
    )

    # Prepare tool environment, including the Python library load path,
    # determining the tool base folder path, and importing task package(s).
    tool_env = initialization.prepare_tool_environment(
        tool_name=meta.tool_name,
        script_path=Path(script_path),
    )

    # Prepare runtime tasks.
    runtime_root_task = initialization.prepare_tasks(
        task_tree=task_tree,
        tool_env=tool_env,
    )

    # Create aliases and parameters catalog classes.
    aliases_catalog = initialization.create_aliases_catalog(
        meta.aliases_catalog_path,
    )
    params_catalog = initialization.create_params_catalog(
        catalog_path=meta.params_catalog_path,
        defaults=param_defaults,
        comments=param_comments,
    )

    # Expand alias as needed and provide 'help' as default command.
    arguments = initialization.prepare_arguments(
        arguments=driver.preliminary_app_data.additional_arguments,
        aliases_catalog=aliases_catalog,
        runtime_root_task=runtime_root_task,
    )

    # Initialize driver to access app data object and help generator.
    driver.initialize_application(
        arguments=arguments,
        root_task=runtime_root_task,
    )

    # Initialize application and prepare Runtime API object.
    runtime = initialization.prepare_runtime(
        runtime_spec=custom.runtime,
        meta=meta,
        venv_folder=venv_folder,
        base_folder=tool_env.base_folder,
        build_folder=build_folder,
        doc_folder=doc_folder,
        test_folder=test_folder,
        driver=driver,
        aliases_catalog=aliases_catalog,
        params_catalog=params_catalog,
        root_task=runtime_root_task,
    )

    # Execute application.
    execution.execute_application(
        task_stack=driver.app_data.task_stack,
        runtime=runtime,
    )


def jiigrun_main(skip_venv_check: bool = False):
    """jiigrun script main.

    Called by tool scripts having "jiigrun" as the "shebang" line interpreter.
    The script's embedded configuration serves as the basis for generating tool
    runtime data.

    Checking for a virtual environment is optional, because when Jiig is
    installed it shouldn't require it, and a virtual environment may be provided
    by the user.

    Args:
        skip_venv_check: skip check for running in a Jiig virtual environment if
            True
    """
    runner_args = sys.argv[:2]
    cli_args = sys.argv[2:]
    if len(runner_args) < 2 or not os.path.isfile(runner_args[1]):
        _fatal('This program should only be used as a script "shebang" line interpreter.')
    script_path = Path(runner_args[1]).resolve()

    # TOML configuration data can either be embedded in the script or in a
    # separate file.
    config_data = _read_script_configuration(script_path)
    extractor = _ConfigurationDataExtractor(config_data)

    options = ToolOptions(
        disable_debug=extractor.boolean('options.disable_debug', False),
        disable_dry_run=extractor.boolean('options.disable_dry_run', False),
        disable_verbose=extractor.boolean('options.disable_verbose', False),
        enable_pause=extractor.boolean('options.enable_pause', False),
        enable_keep_files=extractor.boolean('options.enable_keep_files', False),
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
    )

    task_tree = extractor.task_tree('tasks', DEFAULT_ROOT_TASK_NAME)
    param_defaults, param_comments = extractor.params('params')

    tool_main(
        meta=meta,
        task_tree=task_tree,
        venv_folder=extractor.path('venv_folder'),
        script_path=script_path,
        build_folder=extractor.path('build_folder'),
        doc_folder=extractor.path('doc_folder'),
        test_folder=extractor.path('test_folder'),
        runner_args=runner_args,
        cli_args=cli_args,
        options=options,
        custom=custom,
        param_defaults=param_defaults,
        param_comments=param_comments,
        skip_venv_preparation=skip_venv_check,
    )
