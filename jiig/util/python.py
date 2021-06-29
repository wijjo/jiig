"""
Python interpreter utilities.
"""

import importlib.util
import os
import sys
import traceback
from dataclasses import fields, is_dataclass
from inspect import isclass, isfunction
from types import ModuleType
from typing import Text, List, Tuple, Optional, IO, Dict, Type, Any, TypeVar

from . import OPTIONS
from .log import abort, log_error, log_message, log_warning
from .filesystem import delete_folder, short_path
from .general import format_message_block, plural
from .process import run
from .stream import open_text_source

PYTHON_NATIVE_ENVIRONMENT_NAME = 'JIIG_NATIVE_PYTHON'


def format_call_string(call_name: Text, *args, **kwargs) -> Text:
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


def module_path_to_name(path: Text) -> Text:
    """
    Convert module path to name.

    :param path: module path
    :return: name (always returns something)
    """
    names = [os.path.splitext(os.path.basename(path))[0]]
    folder = os.path.dirname(path)
    while os.path.exists(os.path.join(folder, '__init__.py')):
        names.insert(0, os.path.basename(folder))
        parent_folder = os.path.dirname(folder)
        if parent_folder == folder:
            break
        folder = parent_folder
    return '.'.join(names)


def import_module_path(module_path: Text, module_name: Text = None) -> ModuleType:
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


def import_modules_from_folder(folder: Text,
                               package_name: Text = None,
                               retry: bool = False,
                               ) -> List[Text]:
    """
    Dynamically and recursively import modules from a folder.

    :param folder: search root folder
    :param package_name: optional container package name
    :param retry: retry modules with ModuleNotFoundError exceptions if True
    :return: imported paths
    """
    # Stage 1 - gather the list of module paths and names to import.
    log_message(f'import_modules_from_folder({package_name}, {folder})', debug=True)
    to_import: List[Tuple[Text, Text]] = []
    imported: List[Text] = []
    for walk_folder, _walk_sub_folders, walk_file_names in os.walk(folder):
        if os.path.basename(walk_folder).startswith('_'):
            continue
        relative_folder = walk_folder[len(folder) + 1:]
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
    retry_count: Optional[int] = None
    exceptions: List[Tuple[Text, Text, Exception]] = []
    while to_import:
        to_retry: List[Tuple[Text, Text]] = []
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


def execute_source(*,
                   text: Text = None,
                   file: Text = None,
                   stream: IO = None,
                   symbols: Dict = None) -> Dict:
    """Execute python source code text, file, or stream"""
    exec_symbols = symbols or {}
    with open_text_source(text=text, file=file, stream=stream, check=True) as text_stream:
        # noinspection PyBroadException
        try:
            exec(text_stream.read(), exec_symbols)
            return exec_symbols
        except Exception:
            if text:
                source = '(text)'
            elif file:
                source = short_path(file)
            elif stream:
                source = '(stream)'
            traceback.print_exc()
            abort(f'Unable to execute Python script: {source}')
            sys.exit(1)


def build_virtual_environment(venv_folder: Text,
                              packages: List = None,
                              rebuild: bool = False,
                              quiet: bool = False):
    pip_path = os.path.join(venv_folder, 'bin', 'pip')
    venv_short_path = short_path(venv_folder, is_folder=True)
    if os.path.exists(os.path.join(venv_folder, 'bin', 'python')):
        if not rebuild:
            if not quiet:
                log_message('Virtual environment already exists.', venv_short_path)
            if packages:
                install_missing_virtual_environment_packages(venv_folder, packages, quiet=quiet)
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
    log_message('Upgrade pip in virtual environment.', verbose=True)
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        log_message('Install pip packages in virtual environment.', verbose=True)
        run([pip_path, 'install'] + packages)


def install_missing_virtual_environment_packages(venv_folder: Text,
                                                 packages: List[Text],
                                                 quiet: bool = False):
    if not packages:
        return
    pip_path = os.path.join(venv_folder, 'bin', 'pip')
    result = run([pip_path, 'list'], capture=True, quiet=quiet, run_always=True)
    installed = set()
    for line in result.stdout.split(os.linesep)[2:]:
        columns = line.split(maxsplit=1)
        if len(columns) == 2:
            installed.add(columns[0].lower())
    new_packages = list(filter(lambda p: p.lower() not in installed, packages))
    if not new_packages:
        return
    pip_args = [pip_path, 'install']
    if quiet:
        pip_args.append('-q')
    pip_args.extend(new_packages)
    run(pip_args)


def update_virtual_environment(venv_folder: Text, packages: List = None):
    pip_path = os.path.join(venv_folder, 'bin', 'pip')
    venv_short_path = short_path(venv_folder, is_folder=True)
    if not os.path.isdir(venv_folder) or not os.path.isfile(pip_path):
        abort('Virtual environment is missing or incomplete.', venv_short_path)
    log_message('Update virtual environment', venv_short_path)
    log_message('Upgrade pip in virtual environment.', verbose=True)
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        log_message('Install pip packages in virtual environment.', verbose=True)
        run([pip_path, 'install'] + packages)


T_dataclass = TypeVar('T_dataclass')


def symbols_to_dataclass(symbols: Dict,
                         dc_type: Type[T_dataclass],
                         from_uppercase: bool = False,
                         required: List[Text] = None,
                         optional: List[Text] = None,
                         protected: List[Text] = None,
                         overflow: Text = None,
                         defaults: Dict = None,
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
    :return: populated dataclass instance
    :raise ValueError: if conversion fails due to bad input data
    :raise TypeError: if conversion fails due to bad output type
    """
    if not isclass(dc_type) or not is_dataclass(dc_type):
        raise AttributeError(f'module_to_dataclass() target is not a dataclass.')

    def _is_wanted(item_name: Text, item_value: Any) -> bool:
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
            attribute_word = plural('attribute', missing_names)
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
    unknown_keys: List[Text] = []
    for name in set(input_symbols.keys()).difference(valid_names):
        if overflow:
            if from_uppercase:
                name = name.lower()
            output_symbols.setdefault(overflow, {})[name] = input_symbols[name]
        else:
            unknown_keys.append(name)
    if unknown_keys:
        log_warning(f'Unknown {plural("key", unknown_keys)} in {dc_type.__name__} source'
                    f' dictionary: {" ".join(sorted(unknown_keys))}', symbols)

    try:
        return dc_type(**output_symbols)
    except Exception as exc:
        abort(f'Failed to construct {dc_type.__name__} object.', exc)


def module_to_dataclass(module: object,
                        dc_type: Type[T_dataclass],
                        required: List[Text] = None,
                        protected: List[Text] = None,
                        overflow: Text = None,
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


def load_configuration_script(script_path: Text, **default_symbols) -> Dict:
    """
    Load a Python syntax configuration script.

    :param script_path: script path
    :param default_symbols: default symbols
    :return: symbols from script and defaults
    """
    symbols = dict(default_symbols)
    try:
        with open(file=script_path) as script_file:
            exec(script_file.read(), symbols)
            return symbols
    except Exception as script_exc:
        abort(f'Failed to load script: {script_path}',
              script_exc,
              exec_file_name=script_path,
              exception_traceback_skip=1)
