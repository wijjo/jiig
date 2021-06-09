"""
Runtime execution and symbol expansion context.
"""

from typing import Optional

from jiig.util.action_context import ActionContext
from jiig.util.context import Context

from .options import Options
from .runtime_options import RuntimeOptions


class RuntimeContext(ActionContext):
    """Nestable runtime context for context-sensitive symbol expansion."""

    def __init__(self, parent: Optional[Context], **kwargs):
        """
        Construct runtime context.

        The primary purpose of this ActionContext subclass is to expose runtime
        flags to user applications.

        :param parent: parent context for symbol inheritance
        :param kwargs: initial symbols
        """
        self.options = RuntimeOptions(Options.debug,
                                      Options.dry_run,
                                      Options.verbose,
                                      Options.pause)
        super().__init__(parent, **kwargs)
