"""
General-purpose utility functions and classes.

IMPORTANT: Keep this generic, and make sure it only depends on the Python
standard library, in its most basic form. E.g. don't import `yaml` here. The
jiig script may import this module when running under the system interpreter,
before re-invoking itself in the virtual environment.
"""
import sys
import os
from io import StringIO

import importlib.util
import json
import re
import shlex
import subprocess
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from glob import glob
from string import Template
from typing import Text, List, Dict, Any, Optional, Tuple, IO, Iterator
from urllib.request import urlopen, Request
from urllib.error import URLError

from . import constants


class Regex:
    remote_path = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')
    template_folder_symbol = re.compile(constants.TEMPLATE_FOLDER_SYMBOL_PATTERN)


class AttrDict(dict):

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value


def folder_path(path):
    if not path.endswith('/'):
        path += '/'
    return path


def is_remote_path(path: Text) -> bool:
    return bool(Regex.remote_path.match(path))


def short_path(path, is_folder=False):
    # Special case for remote paths.
    if is_remote_path(path):
        if is_folder:
            return folder_path(path)
        return path
    # Normal handling of local paths.
    path = os.path.abspath(path)
    if path.endswith(os.path.sep):
        path = path[:-1]
    working_folder = os.getcwd()
    if path.startswith(working_folder):
        path = path[len(working_folder) + 1:]
    else:
        parent_folder = os.path.dirname(working_folder)
        if path.startswith(parent_folder):
            path = os.path.join('..', path[len(parent_folder) + 1:])
    if not path:
        path = '.'
    if is_folder or os.path.isdir(path):
        path = folder_path(path)
    return path


def log_message(text: Any, *args, **kwargs):
    """
    Display message line(s) and indented lines for relevant keyword data.

    tag is a special keyword that prefixes all lines in uppercase.
    """

    tag = kwargs.pop('tag', None)
    verbose = kwargs.pop('verbose', None)
    debug = kwargs.pop('debug', None)
    if verbose and not constants.VERBOSE:
        return
    if debug and not constants.DEBUG:
        return
    lines = []
    if text:
        if isinstance(text, (list, tuple)):
            lines.extend(text)
        else:
            lines.append(str(text))
    for value in args:
        lines.append('  {}'.format(value))
    for key, value in kwargs.items():
        if isinstance(value, (list, tuple)):
            for idx, sub_value in enumerate(value):
                lines.append('  {}[{}] = {}'.format(key, idx + 1, sub_value))
        else:
            lines.append('  {} = {}'.format(key, value))
    for line in lines:
        if tag:
            print('{}: {}'.format(tag.upper(), line))
        else:
            print(line)


def abort(text: Any, *args, **kwargs):
    """Display, and in the future log, a fatal error message (to stderr) and quit."""
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    log_message(text, *args, **kwargs)
    if constants.DEBUG:
        print_call_stack(skip=skip + 2)
    sys.exit(255)


def log_warning(text: Any, *args, **kwargs):
    """Display, and in the future log, a warning message (to stderr)."""
    kwargs['tag'] = 'WARNING'
    log_message(text, *args, **kwargs)


def log_error(text: Any, *args, **kwargs):
    """Display, and in the future log, an error message (to stderr)."""
    kwargs['tag'] = 'ERROR'
    log_message(text, *args, **kwargs)


def log_heading(level: int, heading: Text):
    """Display, and in the future log, a heading message to delineate blocks."""
    decoration = '=====' if level == 1 else '---'
    print(f'{decoration} {heading} {decoration}')


def execute_source(*, text: Text = None, file: Text = None, stream: IO = None) -> Dict:
    """Execute python source code text, file, or stream"""
    symbols = {}
    with open_text(text=text, file=file, stream=stream) as text_stream:
        # noinspection PyBroadException
        try:
            exec(text_stream.read(), symbols)
            return symbols
        except Exception:
            if text:
                source = '(text)'
            elif file:
                source = short_path(file)
            elif stream:
                source = '(stream)'
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log_error(f'{source}.{exc_traceback.tb_lineno}: {exc_type.__name__}: {exc_value}')
            abort(f'Unable to execute Python script: {source}')
            sys.exit(1)


def print_call_stack(skip: int = 0, limit: int = None):
    print('  ::Call Stack::')
    for file, line, function, source in traceback.extract_stack(limit=limit)[:-skip]:
        print('  {}.{}, {}()'.format(file, line, function))


@contextmanager
def chdir(folder: Optional[Text]):
    """
    Change work folder and restore when done.

    Treats an empty or None folder, or when folder is the current work folder, a
    do-nothing operation. But at least the caller doesn't have to check.
    """
    restore_folder = os.getcwd()
    if folder and os.path.realpath(folder) != restore_folder:
        log_message('Change working directory.', folder)
        os.chdir(folder)
    yield restore_folder
    if folder and os.path.realpath(folder) != restore_folder:
        log_message('Restore working directory.', restore_folder)
        os.chdir(restore_folder)


@dataclass
class CurlResponse:
    text: Text
    status: int
    reason: Text


def curl(url: Text):
    """Download from a URL and return a CurlResponse object."""
    try:
        response = urlopen(url)
        return CurlResponse(
            response.read().decode('utf-8'),
            getattr(response, 'status', None),
            getattr(response, 'reason', None),
        )
    except URLError as exc:
        abort('cURL failed', url, exception=exc)


def delete_folder(path: Text, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if os.path.exists(path):
        if not quiet:
            log_message('Delete folder and contents.', path)
        run(['rm', '-rf', path])


def delete_file(path: Text, quiet: bool = False):
    path = short_path(path)
    if os.path.exists(path):
        if not quiet:
            log_message('Delete file.', path)
        run(['rm', '-f', path])


def create_folder(path: Text, delete_existing: bool = False, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if delete_existing:
        delete_folder(path, quiet=quiet)
    if not os.path.exists(path):
        if not quiet:
            log_message('Create folder.', folder_path(path))
        run(['mkdir', '-p', path])
    elif not os.path.isdir(path):
        abort('Path is not a folder', path)


def check_file_exists(path: Text):
    if not os.path.exists(path):
        abort('File does not exist.', path)
    if not os.path.isfile(path):
        abort('Path is not a file.', path)


def check_folder_exists(path: Text):
    if not os.path.exists(path):
        abort('Folder does not exist.', path)
    if not os.path.isdir(path):
        abort('Path is not a folder.', path)


def check_file_not_exists(path: Text):
    if os.path.exists(path):
        if os.path.isdir(path):
            abort('File path already exists as a folder.', path)
        abort('File already exists.', path)


def check_folder_not_exists(path: Text):
    if os.path.exists(path):
        if not os.path.isdir(path):
            abort('Folder path already exists as a file.', path)
        abort('Folder already exists.', path)


def copy_folder(src_path: Text,
                dst_path: Text,
                merge: bool = False,
                quiet: bool = False):
    src_folder_path = short_path(src_path, is_folder=True)
    dst_folder_path = short_path(dst_path, is_folder=True)
    if not constants.DRY_RUN:
        check_folder_exists(src_folder_path)
    if not merge:
        delete_folder(dst_path, quiet=quiet)
    create_folder(os.path.dirname(dst_path), quiet=quiet)
    if not quiet:
        log_message('Folder copy.',
                    source=folder_path(src_folder_path),
                    target=folder_path(dst_folder_path))
    if os.path.isdir(dst_folder_path):
        run(['rsync', '-aq', src_folder_path, dst_folder_path])
    else:
        run(['cp', '-a', src_folder_path, dst_folder_path])


def copy_files(src_glob: Text,
               dst_path: Text,
               allow_empty: bool = False,
               quiet: bool = False):
    src_paths = glob(src_glob)
    if not src_paths and not allow_empty:
        abort('File copy source is empty.', src_glob)
    create_folder(dst_path, quiet=quiet)
    if not quiet:
        log_message('File copy.',
                    source=short_path(src_glob),
                    target=short_path(dst_path, is_folder=True))
    for src_path in src_paths:
        run(['cp', short_path(src_path), short_path(dst_path, is_folder=True)])


def move_file(src_path: Text,
              dst_path: Text,
              overwrite: bool = False,
              quiet: bool = False):
    """Move a file to a fully-specified file path, not a folder."""
    src_path_short = short_path(src_path, is_folder=False)
    dst_path_short = short_path(dst_path, is_folder=False)
    if not constants.DRY_RUN:
        check_file_exists(src_path_short)
    if overwrite:
        # If overwriting is allowed a file (only) can be clobbered.
        if os.path.exists(dst_path) and not constants.DRY_RUN:
            check_file_exists(dst_path)
    else:
        # If overwriting is prohibited don't clobber anything.
        if not constants.DRY_RUN:
            check_file_not_exists(dst_path_short)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    run(['mv', '-f', src_path_short, dst_path_short])


def move_folder(src_path: Text,
                dst_path: Text,
                overwrite: bool = False,
                quiet: bool = False):
    """Move a folder to a fully-specified folder path, not a parent folder."""
    src_path_short = short_path(src_path, is_folder=True)
    dst_path_short = short_path(dst_path, is_folder=True)
    if not constants.DRY_RUN:
        check_folder_exists(src_path_short)
    if overwrite:
        delete_folder(dst_path, quiet=quiet)
    else:
        if not constants.DRY_RUN:
            check_folder_not_exists(dst_path_short)
    parent_folder = os.path.dirname(dst_path)
    if not os.path.exists(parent_folder):
        create_folder(parent_folder, quiet=quiet)
    run(['mv', '-f', src_path_short, dst_path_short])


def sync_folders(src_folder: Text,
                 dst_folder: Text,
                 exclude: List = None,
                 check_contents: bool = False,
                 show_files: bool = False,
                 quiet: bool = False):
    # Add the trailing slash for rsync. This works for remote paths too.
    src_folder = folder_path(src_folder)
    dst_folder = folder_path(dst_folder)
    if not constants.DRY_RUN:
        check_folder_exists(src_folder)
    if not quiet:
        log_message('Folder sync.',
                    source=src_folder,
                    target=dst_folder,
                    exclude=exclude or [])
    cmd_args = ['rsync']
    if constants.DRY_RUN:
        cmd_args.append('--dry-run')
    cmd_args.extend(['-a', '--stats', '-h'])
    if check_contents:
        cmd_args.append('-c')
    if show_files:
        cmd_args.append('-v')
    if exclude:
        for excluded in exclude:
            cmd_args.extend(['--exclude', excluded])
    cmd_args.extend([src_folder, dst_folder])
    run(cmd_args)


def expand_template(source_path: Text,
                    target_path: Text,
                    overwrite: bool = False,
                    executable: bool = False,
                    symbols: Dict = None,
                    source_relative_to: Text = None,
                    target_relative_to: Text = None):
    if source_relative_to:
        short_source_path = source_path[len(source_relative_to) + 1:]
    else:
        short_source_path = short_path(source_path)
    if target_relative_to:
        short_target_path = target_path[len(target_relative_to) + 1:]
    else:
        short_target_path = short_path(target_path)
    symbols = symbols or {}
    if not constants.DRY_RUN:
        check_file_exists(source_path)
    if os.path.exists(target_path):
        if not os.path.isfile(target_path):
            abort('Template expansion target exists, but is not a file',
                  short_target_path)
        if not overwrite:
            log_message('Template expansion target exists - skipping',
                        short_target_path)
            return
    log_message('Generate from template.',
                source=short_source_path,
                target=short_target_path)
    if not constants.DRY_RUN:
        try:
            with open(source_path, encoding='utf-8') as src_file:
                with open(target_path, 'w', encoding='utf-8') as target_file:
                    output_text = Template(src_file.read()).substitute(symbols)
                    target_file.write(output_text)
                if executable:
                    os.system('chmod +x {}'.format(target_path))
        except KeyError as exc_key_error:
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except (IOError, OSError) as exc_remove:
                    log_warning('Unable to remove failed target file.',
                                short_target_path,
                                exception=exc_remove)
            abort('Missing template symbol',
                  source=short_source_path,
                  symbol=exc_key_error)
        except (IOError, OSError) as exc_write_error:
            abort('Template expansion failed',
                  source=short_source_path,
                  target=short_target_path,
                  exception=exc_write_error)


def expand_templates(source_glob: Text,
                     target_folder_path: Text,
                     overwrite: bool = False,
                     executable: bool = False,
                     symbols: Dict = None):
    for source_path in glob(source_glob):
        target_path = os.path.join(target_folder_path, os.path.basename(source_path))
        expand_template(source_path,
                        target_path,
                        overwrite=overwrite,
                        executable=executable,
                        symbols=symbols)


def expand_template_path(source_path: Text, symbols: Dict) -> Text:
    """
    Expand name symbols in path.

    :param source_path: source path with potential symbols to expand
    :param symbols: symbol substitution dictionary
    :return: output path with symbols expanded
    """
    name_parts = []
    pos = 0
    for match in Regex.template_folder_symbol.finditer(source_path):
        name = match.group(1)
        start_pos, end_pos = match.span()
        if start_pos > pos:
            name_parts.append(source_path[pos:start_pos])
        if name in symbols:
            name_parts.append(symbols[name])
        else:
            log_error(f'Symbol "{name}" not found for path template "{source_path}".')
            name_parts.append(source_path[start_pos:end_pos])
        pos = end_pos
    if pos < len(source_path):
        name_parts.append(source_path[pos:])
    return ''.join(name_parts)


def expand_template_folder(template_folder: Text,
                           target_folder: Text,
                           overwrite: bool = False,
                           symbols: Dict = None):
    """
    Recursively populate a target folder based on a template folder.

    Note that .template* extensions are removed with special extensions handled
    for generating dot name prefixes and setting executable permissions.

    Source folder names may take advantage of symbol expansion by using special
    syntax for name substitution. Target folder names will receive any
    substituted symbols.

    :param template_folder: path to template source folder
    :param target_folder: path to target folder
    :param overwrite: overwrite files if True
    :param symbols: symbols for template expansion
    :return:
    """
    symbols = symbols or {}
    if not os.path.isdir(template_folder):
        abort('Template source folder does not exist',
              source_folder=folder_path(template_folder))
    if os.path.exists(target_folder):
        if not os.path.isdir(target_folder):
            abort('Template target folder exists, but is not a folder',
                  target_folder=target_folder)
    log_heading(2, f'Expanding templates.')
    log_message(None, template_folder=template_folder, target_folder=target_folder)
    create_folder(target_folder)
    for walk_source_folder, _walk_sub_folders, walk_file_names in os.walk(template_folder):
        relative_folder = walk_source_folder[len(template_folder) + 1:]
        expanded_folder = expand_template_path(relative_folder, symbols)
        walk_target_folder = os.path.join(target_folder, expanded_folder)
        create_folder(walk_target_folder)
        for file_name in walk_file_names:
            source_path = os.path.join(walk_source_folder, file_name)
            stripped_file_name, extension = os.path.splitext(file_name)
            if extension in constants.ALL_TEMPLATE_EXTENSIONS:
                if extension == constants.TEMPLATE_EXTENSION_DOT:
                    stripped_file_name = '.' + stripped_file_name
                expanded_file_name = expand_template_path(stripped_file_name, symbols)
                target_path = os.path.join(walk_target_folder, expanded_file_name)
                executable = extension == constants.TEMPLATE_EXTENSION_EXE
                expand_template(source_path,
                                target_path,
                                overwrite=overwrite,
                                executable=executable,
                                symbols=symbols,
                                source_relative_to=template_folder,
                                target_relative_to=target_folder)
            else:
                copy_files(source_path, walk_target_folder)


def run(cmd_args: List[Text],
        unchecked: bool = False,
        replace_process: bool = False,
        working_folder: Text = None,
        env: Dict = None,
        host: Text = None,
        shell: bool = False,
        run_always: bool = False,
        quiet: bool = False,
        capture: bool = False,
        ) -> Optional[subprocess.CompletedProcess]:
    if not cmd_args:
        abort('Called run() without a command.')
    if not isinstance(cmd_args, (tuple, list)):
        abort('Called run() with a non-list/tuple.', cmd_args=cmd_args)
    if host:
        if shell or env or working_folder:
            abort('Remote run() command, i.e. with "host" specified, may not'
                  ' use "shell", "env", or "working_folder" keywords.',
                  cmd_args=cmd_args)
    # The command string for display or shell execution.
    cmd_string = ' '.join([shlex.quote(arg)
                           for arg in [short_path(cmd_args[0])] + cmd_args[1:]])
    # Adjust remote command to run through SSH.
    if host:
        cmd_args = ['ssh', host] + cmd_args
    # Log message about impending command and run options.
    message_data = {}
    if env:
        message_data['environment'] = ' '.join([
            '{}={}'.format(name, shlex.quote(value))
            for name, value in env.items()])
    if host:
        message_data['host'] = host
    if replace_process:
        message_data['exec'] = 'yes'
    if quiet:
        message_data['verbose'] = True
    log_message('Run command.', cmd_string, **message_data)
    # A dry run can stop here, before taking real action.
    if constants.DRY_RUN and not run_always:
        return None
    # Generate the command run environment.
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    # Set a temporary working folder, if specified.
    if working_folder:
        if not os.path.isdir(working_folder):
            abort('Desired working folder does not exist',
                  folder_path(working_folder))
        restore_folder = os.getcwd()
        os.chdir(working_folder)
    else:
        restore_folder = None
    # Run the command with process replacement.
    if replace_process:
        os.execlp(cmd_args[0], *cmd_args)
    # Or run the command and continue.
    try:
        try:
            kwargs = dict(
                check=not unchecked,
                shell=shell,
                env=run_env,
                capture_output=capture,
            )
            if capture:
                kwargs['encoding'] = 'utf-8'
            return subprocess.run(cmd_args, **kwargs)
        except subprocess.CalledProcessError as exc:
            abort('Command failed.', cmd_string, exc)
        except FileNotFoundError as exc:
            abort('Command not found.', cmd_string, exc)
    finally:
        if restore_folder:
            os.chdir(restore_folder)


def run_shell(cmd_args: List[Text],
              unchecked: bool = False,
              working_folder: Text = None,
              replace_process: bool = False,
              run_always: bool = False):
    return run(cmd_args,
               unchecked=unchecked,
               replace_process=replace_process,
               working_folder=working_folder,
               shell=True,
               run_always=run_always)


def run_remote(host: Text,
               cmd_args: List[Text],
               unchecked: bool = False,
               replace_process: bool = False,
               run_always: bool = False):
    return run(cmd_args,
               host=host,
               unchecked=unchecked,
               replace_process=replace_process,
               run_always=run_always)


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


def make_dest_name(*names: Text) -> Text:
    """Produce a dest name based on a name list."""
    prefixed_names = [constants.CLI_DEST_NAME_PREFIX] + [name.upper() for name in names]
    return constants.CLI_DEST_NAME_SEPARATOR.join(prefixed_names)


def append_dest_name(dest_name: Text, *names: Text) -> Text:
    """Add to an existing dest name."""
    return constants.CLI_DEST_NAME_SEPARATOR.join(
        [dest_name] + [name.upper() for name in names])


def make_metavar(*names: Text) -> Text:
    """Produce a metavar name based on a name list."""
    suffixed_names = [name.upper() for name in names] + [constants.CLI_METAVAR_SUFFIX]
    return constants.CLI_METAVAR_SEPARATOR.join(suffixed_names)


def import_module_path(module_name: Text, module_path: Text):
    """Dynamically import a module by name and path."""
    log_message(f'import_module_path({module_name}, {module_path})', debug=True)
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
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
                if constants.DEBUG:
                    raise
            except Exception as exc:
                exceptions.append((module_name, module_path, exc))
                if constants.DEBUG:
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


def format_call_string(name: Text, *args, **kwargs) -> Text:
    parts = []
    if args:
        parts.append(str(list(args))[1:-1])
    if kwargs:
        parts.append(str(kwargs)[1:-1])
    arg_body = ', '.join(parts)
    return f'{name}({arg_body})'


def get_folder_stack(folder: Text) -> List[Text]:
    """
    Get a list of folders from top-most down to the one provided.

    TODO: This needs a little work for Windows compatibility!

    :param folder: bottom-most folder
    :return: top-to-bottom folder list
    """
    folders = []
    while True:
        head, tail = os.path.split(folder)
        if not tail:
            break
        folders.append(folder)
        folder = head
    return list(reversed(folders))


def load_json_file_stack(file_name: Text, folder: Text = None) -> Dict:
    """
    Load JSON data from file in folder and containing folders.

    JSON data in each discovered file must be wrapped in a dictionary.

    Traversal is top-down so that data from the closest file takes precedence
    over (and overwrites) data from files that are farther up the stack.

    List elements with common names in multiple files are concatenated.

    Dictionary elements with common names in multiple files are merged.

    Scalar value elements keep only the named value from the closest file.

    :param file_name: file name to look for in each folder of the stack
    :param folder: bottom folder of the search stack, defaults to working folder
    :return: merged data dictionary
    """
    folder_stack = get_folder_stack(os.path.abspath(folder) if folder else os.getcwd())
    data = {}
    for stack_folder in folder_stack:
        path = os.path.join(stack_folder, file_name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as config_file:
                config_data = json.load(config_file)
                if not isinstance(config_data, dict):
                    log_error(f'JSON file "{path}" is not a dictionary.')
                    continue
                for key, value in config_data.items():
                    if key in data:
                        if isinstance(value, list):
                            if isinstance(data[key], list):
                                data[key].extend(value)
                            else:
                                log_error(f'Ignoring non-list value'
                                          f' for "{key}" in "{path}".')
                        elif isinstance(value, dict):
                            if isinstance(data[key], dict):
                                data[key].update(value)
                            else:
                                log_error(f'Ignoring non-dictionary value'
                                          f' for "{key}" in "{path}".')
                        else:
                            data[key] = value
                    else:
                        data[key] = value
        except Exception as exc:
            log_error(f'Failed to load JSON file "{path}".',
                      exception=exc)
    return data


@contextmanager
def open_text(*,
              text: Text = None,
              file: Text = None,
              stream: IO = None,
              url: Text = None,
              request: Request = None,
              timeout: int = None) -> Iterator[IO]:
    """
    Open a text stream, given a string, file path, stream, URL, or Request object.

    :param text: input string
    :param file: file path
    :param stream: input stream
    :param url: input URL for downloading
    :param request: input Request object for downloading
    :param timeout: timeout in seconds when downloading URL or Request
    :return: a yielded stream to use in a `with` block for proper closing

    Generates a RuntimeError if one and only one input keyword is not specified.

    Depending on the input type, various kinds of I/O exceptions are possible.
    """
    if len([arg for arg in (text, file, stream, url, request)
            if arg is not None]) != 1:
        raise RuntimeError(f'Exactly one of the following keywords is required:'
                           f' text, file, stream, url, or request')
    if text is not None:
        yield StringIO(text)
    elif file is not None:
        with open(file, encoding='utf-8') as file_stream:
            yield file_stream
    elif stream is not None:
        yield stream
    elif url is not None:
        with urlopen(url, timeout=timeout) as url_stream:
            yield url_stream
    elif request is not None:
        with urlopen(url, timeout=timeout) as request_stream:
            yield request_stream


def resolve_paths_abs(root: Text, folders: Optional[List[Text]]) -> Iterator[Text]:
    """Generate folder sequence with absolute paths."""
    if folders:
        for folder in folders:
            if os.path.isabs(folder):
                yield folder
            else:
                yield os.path.join(root, folder)
