"""
Pdoc3 documentation server task.
"""

import jiig


TASK = jiig.Task(
    description='Use Pdoc3 to serve documentation using HTTP.',
    args={
        'PORT': ('-p', '--port', 'HTTP server port (default: 8080)', int),
    },
)


# For type inspection assistance only.
class Data:
    PORT: int


@TASK.run
def task_run(_runner: jiig.Runner, _data: Data):
    raise NotImplementedError
