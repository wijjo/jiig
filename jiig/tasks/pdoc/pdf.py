"""
Pdoc3 PDF documentation generation task.
"""

import jiig


class Task(jiig.Task):
    """Use Pdoc3 to build PDF format documentation."""

    def on_run(self, runtime: jiig.Runtime):
        raise NotImplementedError
