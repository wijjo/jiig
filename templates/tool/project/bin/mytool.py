#!/usr/bin/env python3
"""
mytool Jiig tool script (pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import sys


def main():
    # Add Jiig root to Python path so that Jiig modules can be loaded.
    # Alternatively, can use PYTHONPATH or any other supported mechanism for
    # extending the library load path.
    sys.path.insert(0, 'jiig_root')
    import jiig
    jiig.main(
        jiig.Tool(
            tool_name='mytool',
            tool_root_folder=os.path.dirname(os.path.dirname(__file__)),
            description='mytool description.',
            root_task='mytool.tasks',
            # pip_packages=[],
            # options=jiig.ToolOptions(),
        ),
        jiig.CLIDriver,
    )


if __name__ == '__main__':
    main()
