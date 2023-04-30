import os
import sys
from pathlib import Path

"""Make sure the Jiig package is accessible."""


def _insert_jiig_library_path():
    source_root = Path(__file__).resolve().parent.parent
    if not (source_root / 'jiig' / '__init__.py').is_file():
        sys.stderr.write(f'Unable to import from the Jiig library.{os.linesep}')
        sys.exit(1)
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))


# Make sure it can load Jiig modules.
try:
    import jiig
except ImportError:
    _insert_jiig_library_path()
