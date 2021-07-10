"""
Pdoc3 documentation server task.
"""

import jiig


# noinspection PyUnusedLocal
@jiig.task(
    cli={
        'options': {
            'port': ('-p', '--port'),
        },
    },
)
def server(
    runtime: jiig.Runtime,
    port: jiig.f.integer(),
):
    """
    Use Pdoc3 to serve documentation using HTTP.

    :param runtime: Jiig runtime API.
    :param port: HTTP server port (default: 8080).
    """
    raise NotImplementedError
