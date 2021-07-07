"""
Pdoc3 PDF documentation generation task.
"""

import jiig


@jiig.task
def pdf(_runtime: jiig.Runtime):
    """Use Pdoc3 to build PDF format documentation."""
    raise NotImplementedError
