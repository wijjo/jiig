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

"""
Python interpreter utilities.
"""

import importlib.util
import os
import sys
import traceback
from dataclasses import fields, is_dataclass, MISSING
from importlib import import_module
from inspect import isclass, isfunction, ismodule, signature
from pathlib import Path
from types import ModuleType
from typing import Type, Any, TypeVar, get_type_hints, get_args, Callable, IO, Iterable

from .default import DefaultValue
from .filesystem import delete_folder, short_path
from .log import abort, log_error, log_message, log_warning
from .messages import format_message_block
from .options import OPTIONS
from .process import run
from .stream import open_text_stream
from .text.grammar import pluralize

PYTHON_NATIVE_ENVIRONMENT_NAME = 'JIIG_NATIVE_PYTHON'


def format_call_string(call_name: str, *args, **kwargs) -> str:
    """
    Format name and arguments with call syntax.

    :param call_name: callable name
    :param args: positional arguments
    :param kwargs: keyword arguments
    :return: formatted string
    """
    returned = kwargs.pop('returned', None)
    parts = []
    if args:
        parts.append(str(list(args))[1:-1])
    if kwargs:
        parts.append(str(kwargs)[1:-1])
    arg_body = ', '.join(parts)
    if returned is not None:
        return_string = f' -> {returned}'
    else:
        return_string = ''
    return f'{call_name}({arg_body}){return_string}'


def module_path_to_name(path: str | Path) -> str:
    """
    Convert module path to name.

    :param path: module path
    :return: name (always returns something)
    """
    if not isinstance(path, Path):
        path = Path(path)
    names = [path.stem]
    folder = path.parent
    while (folder / '__init__.py').exists():
        names.insert(0, folder.name)
        parent_folder = folder.parent
        if parent_folder == folder:
            break
        folder = parent_folder
    return '.'.join(names)


def import_module_path(module_path: str | Path,
                       module_name: str = None,
                       ) -> ModuleType:
    """
    Dynamically import a module by name and path.

    :param module_path: module path
    :param module_name: module name (default is based on path)
    :return: imported module
    """
    if module_name is None:
        module_name = module_path_to_name(module_path)
    log_message(f'import_module_path({module_path}, name="{module_name}")', debug=True)
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    # noinspection PyUnresolvedReferences
    module_spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


class ModuleReferenceResolver:
    """Resolve module references and report errors."""

    unresolved_count = 0

    @classmethod
    def resolve(cls,
                reference: str | ModuleType | None,
                ) -> ModuleType | None:
        """
        Resolve module reference to an imported module.

        Dump the Python path when the first import error is encountered.

        :param reference: module reference as string or already-imported module
        :return: imported module or None if the reference could not be resolved
        """
        if reference is None:
            return None
        if ismodule(reference):
            return reference
        if isinstance(reference, str):
            try:
                return import_module(reference)
            except ModuleNotFoundError as exc:
                cls.unresolved_count += 1
                if cls.unresolved_count == 1:
                    log_warning(f'Python path - see import error(s) below:', *sys.path)
                log_error('Failed to import module.',
                          exc,
                          reference=reference,
                          exception_traceback=True,
                          exception_traceback_skip=2,
                          skip_non_source_frames=True)
                return None
            except Exception as exc:
                log_error('Failed to load task module.',
                          exc,
                          reference=reference,
                          exception_traceback=True,
                          exception_traceback_skip=2,
                          skip_non_source_frames=True)
                return None


def import_modules_from_folder(folder: str | Path,
                               package_name: str = None,
                               retry: bool = False,
                               ) -> list[str]:
    """
    Dynamically and recursively import modules from a folder.

    :param folder: search root folder
    :param package_name: optional container package name
    :param retry: retry modules with ModuleNotFoundError exceptions if True
    :return: imported paths
    """
    # Work with path strings here.
    folder = str(folder)
    # Stage 1 - gather the list of module paths and names to import.
    log_message(f'import_modules_from_folder({package_name}, {folder})',
                debug=True)
    to_import: list[tuple[str, str]] = []
    imported: list[str] = []
    for walk_folder, _walk_sub_folders, walk_file_names in os.walk(folder):
        if os.path.basename(walk_folder).startswith('_'):
            continue
        relative_folder = walk_folder[len(str(folder)) + 1:]
        for file_name in walk_file_names:
            base_name, extension = os.path.splitext(file_name)
            if not base_name.startswith('_') and extension == '.py':
                module_path = os.path.join(walk_folder, file_name)
                package_parts = []
                if package_name:
                    package_parts.append(package_name)
                if relative_folder:
                    package_parts.extend(relative_folder.split(os.path.sep))
                package_parts.append(base_name)
                module_name = '.'.join(package_parts)
                to_import.append((module_name, module_path))
    # Stage 2 - attempt the imports and handle errors, optionally with retries.
    retry_count: int | None = None
    exceptions: list[tuple[str, str, Exception]] = []
    while to_import:
        to_retry: list[tuple[str, str]] = []
        for module_name, module_path in to_import:
            try:
                import_module_path(module_name, module_path)
                imported.append(module_path)
            except ModuleNotFoundError as exc:
                # Only module not found errors are retry-able, because they
                # may be due to inter-module dependencies with ordering issues.
                if retry:
                    to_retry.append((module_name, module_path))
                exceptions.append((module_name, module_path, exc))
                if OPTIONS.debug:
                    raise
            except Exception as exc:
                exceptions.append((module_name, module_path, exc))
                if OPTIONS.debug:
                    raise
        to_import = []
        if to_retry:
            # If we're retrying, keep going as long as some failed imports succeeded.
            if retry_count is None or len(to_retry) < retry_count:
                retry_count = len(to_retry)
                to_import = to_retry
                exceptions = []
    # Stage 3 - report remaining exceptions, if any.
    if exceptions:
        log_error(f'{len(exceptions)} exception(s) during folder import:'
                  f' {folder}["{package_name}"]')
        for module_name, module_path, exc in exceptions:
            log_error(f'{module_path}["{module_name}"]: {exc}')
        abort('Module folder import failure.')
    return imported


def execute_source(path_or_stream: str | Path | IO,
                   symbols: dict = None,
                   unchecked: bool = False,
                   ) -> dict:
    """
    Execute python source file.

    :param path_or_stream: source file path or stream
    :param symbols: optional symbol dictionary for exec()
    :param unchecked: pass along exceptions if True, otherwise abort
    :return: post-exec() symbols
    """
    exec_symbols = symbols or {}
    with open_text_stream(path_or_stream, unchecked=unchecked) as text_stream:
        # noinspection PyBroadException
        try:
            exec(text_stream.read(), exec_symbols)
            return exec_symbols
        except Exception:
            if not unchecked:
                traceback.print_exc()
                abort(f'Unable to execute Python script: {path_or_stream}')
                sys.exit(1)
            raise


def build_virtual_environment(venv_folder: str | Path,
                              packages: list = None,
                              rebuild: bool = False,
                              quiet: bool = False,
                              ):
    """
    Build virtual environment.

    :param venv_folder: virtual environment folder path
    :param packages: packages to install in the virtual environment
    :param rebuild: force rebuild if True
    :param quiet: suppress non-error messages if True
    """
    if not isinstance(venv_folder, Path):
        venv_folder = Path(venv_folder)
    pip_path = venv_folder / 'bin' / 'pip'
    venv_short_path = short_path(venv_folder, is_folder=True)
    if (venv_folder / 'bin' / 'python').exists():
        if not rebuild:
            if not quiet:
                log_message('Virtual environment already exists.', venv_short_path)
            if packages:
                install_missing_pip_packages(packages,
                                             venv_folder=venv_folder,
                                             quiet=quiet)
            return
        delete_folder(venv_folder)
    log_message('Create virtual environment', venv_short_path)
    # Jiig records the native Python executable in an environment variable
    # before restarting in a virtual environment to allow use of the native
    # Python executable to rebuild the virtual environment.
    if PYTHON_NATIVE_ENVIRONMENT_NAME in os.environ:
        python_executable = os.environ[PYTHON_NATIVE_ENVIRONMENT_NAME]
    else:
        python_executable = sys.executable
    run([python_executable, '-m', 'venv', venv_folder])
    log_message('Upgrade pip in virtual environment.')
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        log_message('Install pip packages in virtual environment.')
        run([pip_path, 'install'] + packages)


def install_missing_pip_packages(packages: Iterable[str],
                                 venv_folder: str | Path = None,
                                 quiet: bool = False,
                                 ):
    """
    Install missing Pip packages.

    if a virtual environment is specified uses a different/more efficient
    method, rather than executing "pip list".

    :param packages: packages needed
    :param venv_folder: optional virtual environment folder path
    :param quiet: suppress non-error messages if True
    """
    if not packages:
        return
    if venv_folder is None:
        installed = pip_installed_packages()
        pip_path = 'pip'
    else:
        if not isinstance(venv_folder, Path):
            venv_folder = Path(venv_folder)
        installed = virtual_environment_installed_packages(venv_folder)
        pip_path = venv_folder / 'bin' / 'pip'
    new_packages = list(filter(lambda p: p not in installed, packages))
    if not new_packages:
        return
    pip_args = [pip_path, 'install']
    if quiet:
        pip_args.append('-q')
    pip_args.extend(new_packages)
    run(pip_args)


def pip_installed_packages(pip_path: Path | str | None = None,
                           quiet: bool = False,
                           ) -> list[str]:
    """
    Get installed package list by executing "pip list".

    :param pip_path: optional path to pip executable
    :param quiet: suppress non-error messages if True
    """
    if pip_path is None:
        pip_path = 'pip'
    result = run([str(pip_path), 'list'],
                 capture=True,
                 quiet=quiet,
                 run_always=True)
    installed: list[str] = []
    for line in result.stdout.split(os.linesep)[2:]:
        columns = line.split(maxsplit=1)
        if len(columns) == 2:
            installed.append(columns[0].lower())
    return installed


def virtual_environment_installed_packages(venv_folder: Path | str,
                                           quiet: bool = False,
                                           ) -> list[str]:
    """
    Get installed package list directly from virtual environment.

    Loads <venv>/lib/<python>/site-packages/pydeps/

    :param venv_folder: optional virtual environment folder path
    :param quiet: suppress non-error messages if True
    """
    if not isinstance(venv_folder, Path):
        venv_folder = Path(venv_folder)
    lib_folder = venv_folder / 'lib'
    site_packages: Path | None = None
    lib_sub_folders = list(lib_folder.glob('python*'))
    if lib_sub_folders:
        site_packages_path = lib_folder / lib_sub_folders[0] / 'site-packages'
        if site_packages_path.is_dir():
            site_packages = site_packages_path
    if site_packages is None:
        # Panic and fall back to using the pip command.
        log_error(f'Unable to find virtual environment site-packages.',
                  venv_folder=venv_folder)
        pip_path = venv_folder / 'bin' / 'pip'
        if not pip_path.is_file():
            abort('Virtual environment pip command not found.', pip_path)
        return pip_installed_packages(pip_path=pip_path, quiet=quiet)
    return [
        str(dist_info.name).split('-', maxsplit=1)[0]
        for dist_info in site_packages.glob('*.dist-info')
    ]


def update_virtual_environment(venv_folder: str | Path,
                               packages: list = None,
                               ):
    """
    Update packages and pip in virtual environment.

    :param venv_folder: virtual environment folder path
    :param packages: packages needed
    """
    if not isinstance(venv_folder, Path):
        venv_folder = Path(venv_folder)
    pip_path = venv_folder / 'bin' / 'pip'
    venv_short_path = short_path(venv_folder, is_folder=True)
    if not venv_folder.is_dir() or not pip_path.is_file():
        abort('Virtual environment is missing or incomplete.', venv_short_path)
    log_message('Update virtual environment', venv_short_path)
    log_message('Upgrade pip in virtual environment.', verbose=True)
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        log_message('Install pip packages in virtual environment.', verbose=True)
        run([pip_path, 'install'] + packages)


T_dataclass = TypeVar('T_dataclass')


def symbols_to_dataclass(symbols: dict,
                         dc_type: Type[T_dataclass],
                         from_uppercase: bool = False,
                         required: list[str] = None,
                         optional: list[str] = None,
                         protected: list[str] = None,
                         overflow: str = None,
                         defaults: dict = None,
                         ignore_extra_symbols: bool = False,
                         ) -> T_dataclass:
    """
    Populate dataclass from symbols.

    Uppercase module globals become lowercase dataclass attributes.

    The behavior may be altered by optional parameters.

    :param symbols: input symbols
    :param dc_type: output dataclass type, scanned for field names, etc.
    :param from_uppercase: convert from upper to lower case if True
    :param required: list of required dataclass field names
    :param optional: list of optional dataclass field names
    :param protected: list of unwanted dataclass field names
    :param overflow: optional dataclass field name to receive unexpected symbols
    :param defaults: optional defaults that may be used for missing attributes
    :param ignore_extra_symbols: ignore unexpected symbols if True
    :return: populated dataclass instance
    :raise ValueError: if conversion fails due to bad input data
    :raise TypeError: if conversion fails due to bad output type
    """
    if not isclass(dc_type) or not is_dataclass(dc_type):
        raise AttributeError(f'symbols_to_dataclass() target is not a dataclass.')

    def _is_wanted(item_name: str, item_value: Any) -> bool:
        if item_name.startswith('_'):
            return False
        if isfunction(item_value):
            return False
        if from_uppercase and item_name.isupper():
            item_name = item_name.lower()
        if not item_name.islower():
            return False
        if protected and item_name in protected:
            log_warning(f'Ignoring protected symbol "{attr_name}"'
                        f' in {dc_type.__name__} module.')
            return False
        return True

    # Convert symbols and adjust key case as needed.
    input_symbols = {}
    for attr_name, attr_value in symbols.items():
        if _is_wanted(attr_name, attr_value):
            input_symbols[attr_name.lower()] = attr_value

    # Use defaults for missing items.
    if defaults:
        for default_attr_name, default_attr_value in defaults.items():
            if default_attr_name not in input_symbols:
                input_symbols[default_attr_name] = default_attr_value

    # Assign None to missing optional items.
    if optional:
        for optional_attr_name in optional:
            if optional_attr_name not in input_symbols:
                input_symbols[optional_attr_name] = None

    if required:
        # Check for missing required symbols.
        missing_names = set(required).difference(input_symbols.keys())
        if missing_names:
            if from_uppercase:
                missing_names = map(str.upper, missing_names)
            attribute_word = pluralize('attribute', missing_names)
            message = format_message_block(f'{dc_type.__name__} data is missing'
                                           f' the following {attribute_word}:',
                                           *sorted(missing_names))
            raise ValueError(message)

    # Set known output symbols.
    output_symbols = {}
    # noinspection PyDataclass
    valid_names = set(f.name for f in fields(dc_type))
    for name in valid_names.intersection(input_symbols.keys()):
        output_symbols[name] = input_symbols[name]

    # Handle unknown keys as overflow or warnings, based on overflow option.
    unknown_keys: list[str] = []
    for name in set(input_symbols.keys()).difference(valid_names):
        if overflow:
            if from_uppercase:
                name = name.lower()
            output_symbols.setdefault(overflow, {})[name] = input_symbols[name]
        else:
            unknown_keys.append(name)
    if unknown_keys and not ignore_extra_symbols:
        log_warning(f'Unknown {pluralize("key", unknown_keys)} in {dc_type.__name__} source'
                    f' dictionary: {" ".join(sorted(unknown_keys))}', symbols)

    try:
        return dc_type(**output_symbols)
    except Exception as exc:
        abort(f'Failed to construct {dc_type.__name__} object.', exc)


def module_to_dataclass(module: object,
                        dc_type: Type[T_dataclass],
                        required: list[str] = None,
                        protected: list[str] = None,
                        overflow: str = None,
                        ) -> object:
    """
    Populate dataclass from module globals.

    Uppercase module globals become lowercase dataclass attributes.

    The behavior may be altered by optional parameters.

    :param module: input module object
    :param dc_type: output dataclass type, scanned for field names, etc.
    :param required: list of required dataclass field names
    :param protected: list of unwanted dataclass field names
    :param overflow: optional dataclass field name to receive unexpected symbols
    :return: populated dataclass instance
    :raise AttributeError: if conversion fails due to bad input data
    :raise TypeError: if conversion fails due to bad output type
    """
    return symbols_to_dataclass(module.__dict__,
                                dc_type,
                                from_uppercase=True,
                                required=required,
                                protected=protected,
                                overflow=overflow)


def load_configuration_script(script_path: str | Path,
                              **default_symbols,
                              ) -> dict:
    """
    Load a Python syntax configuration script.

    Obviously executing Python code is potentially unsafe.

    :param script_path: script path
    :param default_symbols: default symbols
    :return: symbols from script and defaults
    """
    symbols = dict(default_symbols)
    try:
        with open(script_path, encoding='utf-8') as script_file:
            exec(script_file.read(), symbols)
            return symbols
    except Exception as script_exc:
        abort(f'Failed to load script: {script_path}',
              script_exc,
              string_file_name=script_path,
              exception_traceback_skip=1)


class ExtractedField:
    """Annotation and default for dataclass or function-extracted field."""

    def __init__(self, name: str, hint: Any, default: DefaultValue = None):
        """
        ExtractedField constructor.

        :param name: field name
        :param hint: raw hint (parsed into type hint and annotation)
        :param default: optional default value
        """
        self.name = name
        hint_args = get_args(hint)
        if len(hint_args) == 0:
            self.type_hint = hint
            self.annotation = None
        else:
            self.type_hint = hint_args[0]
            if len(hint_args) == 2:
                self.annotation = hint_args[1]
            else:
                self.annotation = None
        self.default = default


class ExtractedFields:
    """Fields and defaults extracted from dataclass or function signature."""
    def __init__(self):
        self.fields: list[ExtractedField] = []
        self.errors: list[str] = []


def get_dataclass_fields(dataclass_class: Type) -> ExtractedFields:
    """
    Extract fields and defaults from a dataclass.

    :param dataclass_class: dataclass to probe
    :return: Fields object with annotations and defaults by field name, plus error messages
    """
    fields_by_name: dict[str, ExtractedField] = {}
    task_fields = ExtractedFields()
    # Pass 1 - extract type hints.
    for name, type_hint in get_type_hints(dataclass_class, include_extras=True).items():
        extracted_field = ExtractedField(name, type_hint)
        task_fields.fields.append(extracted_field)
        fields_by_name[name] = extracted_field
    # Pass 2 - extract default values.
    # noinspection PyDataclass
    for field in fields(dataclass_class):
        if field.default is not MISSING:
            fields_by_name[field.name].default = DefaultValue(field.default)
        elif field.default_factory is not MISSING:
            fields_by_name[field.name].default = DefaultValue(field.default_factory())
    return task_fields


def get_function_fields(function: Callable) -> ExtractedFields:
    """
    Extract fields and defaults from a function.

    :param function: function to probe
    :return: Fields object with annotations and defaults by field name, plus error messages
    """
    function_signature = signature(function)
    parameters = function_signature.parameters
    errors: list[str] = []
    task_fields = ExtractedFields()
    for idx, parameter_pair in enumerate(parameters.items()):
        name, parameter = parameter_pair
        if parameter.kind in [parameter.VAR_POSITIONAL,
                              parameter.VAR_KEYWORD,
                              parameter.POSITIONAL_ONLY]:
            errors.append('Variable arguments are not supported.')
        elif parameter.annotation is not parameter.empty:
            if parameter.default is not parameter.empty:
                default_value = DefaultValue(parameter.default)
            else:
                default_value = None
            field = ExtractedField(name, parameter.annotation, default=default_value)
            task_fields.fields.append(field)
        else:
            errors.append(f'Parameter "{name}" is not a Jiig field.')
    return task_fields


def find_package_base_folder(package_name: str,
                             start_path: Path | str,
                             ) -> Path | None:
    """
    Look for folder containing named package given a starting path.

    Searches containing folder stack for a sub-folder where it looks like the
    package lives. It returns the containing folder under which the package was
    found.

    :param package_name: dot-separated package name
    :param start_path: start path for search
    :return: containing folder path if resolved or None otherwise
    """
    def _check_folder(folder: Path, names: list[str]) -> Path | None:
        sub_folder = folder / names[0]
        init_path = sub_folder / '__init__.py'
        if init_path.is_file():
            if len(names) == 1:
                return sub_folder
            return _check_folder(sub_folder, names[1:])

    if not isinstance(start_path, Path):
        start_path = Path(start_path)
    if start_path.is_file():
        start_path = start_path.parent
    package_names = package_name.split('.')
    check_folder = start_path
    while True:
        package_folder = _check_folder(check_folder, package_names)
        if package_folder is not None:
            return check_folder
        if check_folder.parent == check_folder:
            break
        check_folder = check_folder.parent
    return None
