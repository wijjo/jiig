"""
Pdoc3 documentation server task.
"""

import jiig


# noinspection PyUnusedLocal
@jiig.task
def server(
    runtime: jiig.Runtime,
    port: jiig.f.integer('HTTP server port (default: 8080)',
                         cli_flags=('-p', '--port')),
):
    """Use Pdoc3 to serve documentation using HTTP."""
    raise NotImplementedError
