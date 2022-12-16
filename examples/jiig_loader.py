"""
Load Jiig by adding as needed to the Python library path.

For access to Jiig library modules from another project:
* Copy this file in your project, e.g. to the top level package folder.
* Import this file at runtime.
"""

import os
import sys
from pathlib import Path
from subprocess import run

CACHE_PATH = Path(__file__).parent / '.jiig_path'


def _validate_folder_path(folder_path_string: str) -> Path | None:
    folder_path_string = folder_path_string.strip()
    folder_path = Path(folder_path_string)
    if (folder_path / 'jiig' / '__init__.py').is_file():
        return folder_path.absolute()
    sys.stderr.write(f'ERROR: Bad Jiig folder path: {folder_path}{os.linesep}')
    return None


def _check_cached_path() -> Path | None:
    if CACHE_PATH.is_file():
        try:
            with open(CACHE_PATH, encoding='utf-8') as cache_file:
                return _validate_folder_path(cache_file.read())
        except (IOError, OSError) as exc:
            sys.stderr.write(f'ERROR: Unable to read Jiig path cache:'
                             f' {CACHE_PATH}: {exc}{os.linesep}')
    return None


def _check_jiig_program_path() -> Path | None:
    try:
        proc = run(['jiig', '--show-library-path'], encoding='utf-8', capture_output=True)
        if proc.returncode == 0:
            folder_path = _validate_folder_path(proc.stdout)
            if folder_path is not None:
                try:
                    with open(CACHE_PATH, 'w', encoding='utf-8',) as cache_file:
                        cache_file.write(f'{folder_path}{os.linesep}')
                except (IOError, OSError) as exc:
                    sys.stderr.write(f'ERROR: Failed to save Jiig path cache:'
                                     f' {CACHE_PATH}: {exc}{os.linesep}')
            return folder_path
        else:
            sys.stderr.write(f'{proc.stderr}{os.linesep}')
            return None
    except (IOError, OSError):
        return None


def initialize_jiig() -> Path | None:
    """
    Determine Jiig library path and add to Python path.

    return: Jiig library path
    """
    jiig_folder_path = _check_cached_path()
    if jiig_folder_path is None:
        proc = run(['jiig', '--library-path'], capture_output=True, encoding='utf-8')
        if proc.returncode == 0:
            jiig_folder_path = _check_jiig_program_path()
        if jiig_folder_path is None:
            sys.stderr.write(f'ERROR: Failed to resolve Jiig library path.{os.linesep}')
            sys.stdout.write(f'--- "jiig --library-path" output ---{os.linesep}')
            if proc.stdout:
                sys.stdout.write(f'{proc.stdout}{os.linesep}')
            if proc.stderr:
                sys.stderr.write(f'{proc.stderr}{os.linesep}')
            sys.stdout.write(f'--- {os.linesep}')
        sys.exit(1)
    if jiig_folder_path is not None and jiig_folder_path not in sys.path:
        sys.path.insert(0, str(jiig_folder_path))
    return jiig_folder_path


initialize_jiig()
