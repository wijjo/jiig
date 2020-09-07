"""Python interpreter utilities."""

import importlib.util
import os
import sys
import traceback
from typing import Text, List, Tuple, Optional, IO, Dict

from jiig.internal import global_data
from .console import abort, log_error, log_message
from .filesystem import delete_folder, short_path
from .process import run
from .stream import open_text


def format_call_string(name: Text, *args, **kwargs) -> Text:
    parts = []
    if args:
        parts.append(str(list(args))[1:-1])
    if kwargs:
        parts.append(str(kwargs)[1:-1])
    arg_body = ', '.join(parts)
    return f'{name}({arg_body})'


def import_module_path(module_name: Text, module_path: Text):
    """Dynamically import a module by name and path."""
    log_message(f'import_module_path({module_name}, {module_path})', debug=True)
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
                if global_data.DEBUG:
                    raise
            except Exception as exc:
                exceptions.append((module_name, module_path, exc))
                if global_data.DEBUG:
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
    with open_text(text=text, file=file, stream=stream, check=True) as text_stream:
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
    def _program_path(name):
        return os.path.join(venv_folder, 'bin', name)
    venv_short_path = short_path(venv_folder, is_folder=True)
    if os.path.exists(_program_path('python')):
        if not rebuild:
            if not quiet:
                log_message('Virtual environment already exists.', venv_short_path)
            return
        delete_folder(venv_folder)
    log_message('Create virtual environment', venv_short_path)
    run([sys.executable, '-m', 'venv', venv_folder])
    pip_path = _program_path('pip')
    log_message('Upgrade pip in virtual environment.', verbose=True)
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        log_message('Install pip packages in virtual environment.', verbose=True)
        run([pip_path, 'install'] + packages)


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
