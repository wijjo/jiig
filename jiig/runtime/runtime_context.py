"""
Runtime context.
"""

from typing import Optional

from jiig.util.contexts import ActionContext, Context

from .runtime_options import Options


class RuntimeContext(ActionContext):
    """Runtime sub-context for context-sensitive symbol expansion."""

    def __init__(self, parent: Optional[Context], **kwargs):
        """
        Construct runtime context.

        The primary purpose of this ActionContext subclass is to expose runtime
        flags to user applications.

        :param parent: parent context for symbol inheritance
        :param kwargs: initial symbols
        """
        self.options = Options
        super().__init__(parent, **kwargs)
