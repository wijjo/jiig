import os
import sys
from pathlib import Path


def check_jiig():
    """Make sure the Jiig package is accessible."""
    # Try to identify Jiig source root.
    jiig_source_root = Path(__file__).resolve().parent.parent
    if not (jiig_source_root / 'jiig' / '__init__.py').is_file():
        jiig_source_root = None
    # Make sure it can load Jiig modules.
    try:
        # Jiig is installed.
        import jiig
    except ImportError:
        # Otherwise adjust Python path to use Jiig source.
        if jiig_source_root is None:
            sys.stderr.write(f'Unable to import from the Jiig library.{os.linesep}')
            sys.exit(1)
        if str(jiig_source_root) not in sys.path:
            sys.path.insert(0, str(jiig_source_root))
