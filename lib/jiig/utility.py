"""
General-purpose utility functions and classes.

IMPORTANT: Keep this generic, and make sure it only depends on the Python
standard library, in its most basic form. E.g. don't import `yaml` here. The
jiig script may import this module when running under the system interpreter,
before re-invoking itself in the virtual environment.
"""
import sys
import os
import importlib.util
import re
import shlex
import subprocess
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from glob import glob
from string import Template
from typing import Text, List, Dict, Any, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError

from . import constants


class Regex:
    remote_path = re.compile(r'^([\w\d.@-]+):([\w\d_-~/]+)$')


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


def display_message(text: Any, *args, **kwargs):
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


def print_call_stack(skip=0, limit=None):
    print('  ::Call Stack::')
    for file, line, function, source in traceback.extract_stack(limit=limit)[:-skip]:
        print('  {}.{}, {}()'.format(file, line, function))


def abort(text: Any, *args, **kwargs):
    skip = kwargs.pop('skip', 0)
    kwargs['tag'] = 'FATAL'
    display_message(text, *args, **kwargs)
    if constants.DEBUG:
        print_call_stack(skip=skip + 2)
    sys.exit(255)


def display_warning(text: Any, *args, **kwargs):
    kwargs['tag'] = 'WARNING'
    display_message(text, *args, **kwargs)


def display_error(text: Any, *args, **kwargs):
    kwargs['tag'] = 'ERROR'
    display_message(text, *args, **kwargs)


def display_heading(level: int, heading: Text):
    decoration = '=====' if level == 1 else '---'
    print(f'{decoration} {heading} {decoration}')


@contextmanager
def chdir(folder):
    restore_folder = os.getcwd()
    if os.path.realpath(folder) != restore_folder:
        display_message('Change working directory.', folder)
        os.chdir(folder)
    yield restore_folder
    if os.path.realpath(folder) != restore_folder:
        display_message('Restore working directory.', restore_folder)
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
            display_message('Delete folder and contents.', path)
        run(['rm', '-rf', path])


def delete_file(path: Text, quiet: bool = False):
    path = short_path(path)
    if os.path.exists(path):
        if not quiet:
            display_message('Delete file.', path)
        run(['rm', '-f', path])


def create_folder(path: Text, keep: bool = False, quiet: bool = False):
    path = short_path(path, is_folder=True)
    if not keep:
        delete_folder(path, quiet=quiet)
    if not os.path.exists(path):
        if not quiet:
            display_message('Create folder.', folder_path(path))
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
    create_folder(os.path.dirname(dst_path), keep=True, quiet=quiet)
    if not quiet:
        display_message('Folder copy.',
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
    create_folder(dst_path, keep=True, quiet=quiet)
    if not quiet:
        display_message('File copy.',
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
        create_folder(parent_folder, keep=True, quiet=quiet)
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
        create_folder(parent_folder, keep=True, quiet=quiet)
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
        display_message('Folder sync.',
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
                    symbols: Dict = None):
    source_path = short_path(source_path)
    target_path = short_path(target_path)
    symbols = symbols or {}
    if not constants.DRY_RUN:
        check_file_exists(source_path)
    if os.path.exists(target_path):
        if not os.path.isfile(target_path):
            abort('Template expansion target exists, but is not a file', target_path)
        if not overwrite:
            display_message('Template expansion target exists - skipping', target_path)
            return
    display_message('Generate from template.', source=source_path, target=target_path)
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
                    display_warning('Unable to remove failed target file.',
                                    target_path, exception=exc_remove)
            abort('Missing template symbol', source=source_path, symbol=exc_key_error)
        except (IOError, OSError) as exc_write_error:
            abort('Template expansion failed',
                  source=source_path, target=target_path, exception=exc_write_error)


def run(cmd_args: List[Text],
        unchecked: bool = False,
        replace_process: bool = False,
        working_folder: Text = None,
        env: Dict = None,
        host: Text = None,
        shell: bool = False,
        run_always: bool = False):
    # TODO: Remote commands don't support all option parameters.
    assert cmd_args
    assert not host or not (shell or env or working_folder)
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
    display_message('Run command.', cmd_string, **message_data)
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
            return subprocess.run(
                cmd_args,
                check=not unchecked,
                shell=shell,
                env=run_env)
        except subprocess.CalledProcessError as exc:
            abort('Command failed', exc)
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
                display_message('Virtual environment already exists.', venv_short_path)
            return
        delete_folder(venv_folder)
    display_message('Create virtual environment', venv_short_path)
    run(['python3', '-m', 'venv', venv_folder])
    pip_path = _program_path('pip')
    display_message('Upgrade pip in virtual environment.', verbose=True)
    run([pip_path, 'install', '--upgrade', 'pip'])
    if packages:
        display_message('Install pip packages in virtual environment.', verbose=True)
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
    display_message(f'import_module_path({module_name}, {module_path})', debug=True)
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def import_modules_from_folder(package_name: Text, folder: Text, retry: bool = False):
    """Dynamically import modules as a named package from a folder."""
    # Stage 1 - gather the list of module paths and names to import.
    to_import: List[Tuple[Text, Text]] = []
    # if os.path.exists(init_path):
    #     to_import.append((package_name, init_path))
    for walk_folder, _walk_sub_folders, walk_file_names in os.walk(folder):
        relative_folder = walk_folder[len(folder):]
        for file_name in walk_file_names:
            base_name, extension = os.path.splitext(file_name)
            if not base_name.startswith('_') and extension == '.py':
                module_path = os.path.join(walk_folder, file_name)
                package_parts = [package_name]
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
            except ModuleNotFoundError as exc:
                # Only module not found errors are retry-able, because they
                # may be due to inter-module dependencies with ordering issues.
                if retry:
                    to_retry.append((module_name, module_path))
                exceptions.append((module_name, module_path, exc))
            except Exception as exc:
                exceptions.append((module_name, module_path, exc))
        to_import = []
        if to_retry:
            # If we're retrying, keep going as long as some failed imports succeeded.
            if retry_count is None or len(to_retry) < retry_count:
                retry_count = len(to_retry)
                to_import = to_retry
                exceptions = []
    # Stage 3 - report remaining exceptions, if any.
    if exceptions:
        display_error(f'{len(exceptions)} exceptions during folder'
                      f' import: {folder}["{package_name}"]')
        for module_name, module_path, exc in exceptions:
            display_error(f'{module_path}["{module_name}"]: {exc}')
        abort('Module folder import failure.')
