"""
Pdoc3 documentation server task.
"""

import jiig


class Task(jiig.Task):
    """Use Pdoc3 to serve documentation using HTTP."""

    port: jiig.integer('HTTP server port (default: 8080)', cli_flags=('-p', '--port'))

    def on_run(self, runtime: jiig.Runtime):
        raise NotImplementedError
