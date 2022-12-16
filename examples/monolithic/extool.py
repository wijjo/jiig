#!/usr/bin/env python3
"""
extool (jiig monolithic tool script - pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import sys

try:
    import jiig
except ImportError:
    sys.stderr.write('''\
ERROR: Unable to import "jiig" module.

Make sure Jiig is installed and consider one of the following measures:

- Set the PYTHONPATH environment variable to include the Jiig root.
- Set sys.path inside the script to include the Jiig root. 
- Install the `jiig` library folder under an existing Python library root.
''')
    sys.exit(1)

from jiig import fields
from jiig.task import task
from jiig.runtime import Runtime
from jiig.tool import Tool
from jiig.startup import main


@task
def calc(
    runtime: Runtime,
    blocks: fields.text(repeat=(1, None)),
):
    """
    evaluate formula using Python interpreter

    :param runtime: jiig runtime api
    :param blocks: formula block(s) to evaluate
    """
    try:
        result = eval(' '.join(blocks))
        runtime.message(f'The result is {result}.')
    except Exception as exc:
        runtime.abort(f'Formula error: {exc}')


@task(
    cli={
        'options': {
            'upper': ('-u', '--upper'),
            'lower': ('-l', '--lower'),
        }
    }
)
def case(
    runtime: Runtime,
    upper: fields.boolean(),
    lower: fields.boolean(),
    blocks: fields.text(repeat=(1, None)),
):
    """
    convert text case (default is "smart" conversion)

    :param runtime: jiig runtime api
    :param upper: convert to all-uppercase
    :param lower: convert to all-lowercase
    :param blocks: text block(s) to convert
    """
    if upper and lower:
        raise RuntimeError('Conflicting upper/lower options specified.')
    if not upper and not lower:
        # "Smart" conversion checks first character of first block.
        to_upper = blocks[0][:1].islower()
    else:
        to_upper = upper
    text = ' '.join(blocks)
    if to_upper:
        output_text = text.upper()
    else:
        output_text = text.lower()
    runtime.message(output_text)


@task
def words(
    runtime: Runtime,
    blocks: fields.text(repeat=(1, None)),
):
    """
    count words using primitive whitespace splitting

    :param runtime: jiig runtime api
    :param blocks: text block(s) with words to count
    """
    count = len(' '.join(blocks).split())
    runtime.message(f'The word count is {count}.')


# noinspection PyUnusedLocal
@task(tasks=(case, words, calc))
def root(runtime: Runtime):
    """
    various text manipulations

    :param runtime: jiig runtime api
    """
    pass


TOOL = Tool(
    tool_name='extool',
    tool_root_folder=os.path.dirname(__file__),
    description='extool description.',
    root_task=root,
    # driver='jiig.driver.cli',
    # driver_variant='argparse',
    # pip_packages=[],
    # options=jiig.ToolOptions(),
)


if __name__ == '__main__':
    main(TOOL)
