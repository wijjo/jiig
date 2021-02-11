#!/usr/bin/env python3
"""
mytool Jiig tool script (pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import jiig

if __name__ == '__main__':
    jiig.main(jiig.Tool(
        tool_name='mytool',
        tool_root_folder=os.path.dirname(__file__),
        description='mytool description.',
        root_task='mytool.task.root',
    ))
