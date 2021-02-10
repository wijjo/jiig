"""
Pdoc3 PDF documentation generation task.
"""

import jiig


TASK = jiig.Task(
    description='Use Pdoc3 to build PDF format documentation.',
)


@TASK.run
def task_run(_runner: jiig.Runner, _data: object):
    raise NotImplementedError
