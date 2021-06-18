#!/usr/bin/env python3
"""
mytool (jiig monolithic tool script - pure-Python version).

PYTHONPATH (i.e. sys.path) must include Jiig lib for `import jiig` to work.

To use a virtual environment, either let `jiig.main()` automatically create and
restart in it or activate the virtual environment prior to running this script.
"""

import os
import sys

# Add Jiig root to Python path so that Jiig modules can be loaded.
# Alternatively, can use PYTHONPATH or any other supported mechanism for
# extending the library load path.
sys.path.insert(0, 'jiig_root')

import jiig     # noqa: E402


class TaskCalc(jiig.Task):
    """Evaluate formula using Python interpreter."""
    blocks: jiig.text('formula block(s) to evaluate', repeat=(1, None))

    def on_run(self, runtime: jiig.Runtime):
        result = eval(' '.join(self.blocks))
        print(f'The result is {result}.')


# noinspection DuplicatedCode
class TaskCase(jiig.Task):
    """Convert text case (default is "smart" conversion)."""
    upper: jiig.boolean('convert to all-uppercase', cli_flags='-u')
    lower: jiig.boolean('convert to all-lowercase', cli_flags='-l')
    blocks: jiig.text('text block(s) to convert', repeat=(1, None))

    def on_run(self, runtime: jiig.Runtime):
        if self.upper and self.lower:
            raise RuntimeError('Conflicting upper/lower options specified.')
        if not self.upper and not self.lower:
            # "Smart" conversion checks first character of first block.
            to_upper = self.blocks[0][:1].islower()
        else:
            to_upper = self.upper
        text = ' '.join(self.blocks)
        if to_upper:
            output_text = text.upper()
        else:
            output_text = text.lower()
        print(output_text)


class TaskWords(jiig.Task):
    """Count words using primitive whitespace splitting."""
    blocks: jiig.text('text block(s) with words to count', repeat=(1, None))

    def on_run(self, _runtime: jiig.Runtime):
        count = len(' '.join(self.blocks).split())
        print(f'The word count is {count}.')


class TaskRoot(jiig.Task,
               tasks={'case': TaskCase,
                      'words': TaskWords,
                      'calc': TaskCalc}
               ):
    """Various text manipulations."""
    pass


TOOL = jiig.Tool(
    tool_name='mytool',
    tool_root_folder=os.path.dirname(__file__),
    description='mytool description.',
    root_task=TaskRoot,
    # pip_packages=[],
    # options=jiig.ToolOptions(),
)


if __name__ == '__main__':
    jiig.main(TOOL, jiig.CLIDriver)
