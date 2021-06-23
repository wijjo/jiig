"""Task handler."""

from .registry import RegisteredTask
from .util.contexts import ActionContext


# The `skip_registration` class keyword argument makes sure this abstract
# intermediate class isn't registered. The concrete sub-class needs to be the
# only one that is registered and wrapped in a dataclass.
class Task(RegisteredTask, skip_registration=True):
    """
    Self-registering base task handler (call-back class).

    Use as a base for registered task classes. It provides type-checked method
    overrides and automatic class registration and wrapping as a dataclass.

    Self-registers sub-classes to the task registry.

    The class declaration accepts the following keyword arguments:
        - description: task description
        - notes: notes list
        - footnotes: footnotes dictionary
        - tasks: sub-tasks dictionary
        - visibility: 0=normal, 1=secondary, 2=hidden
    """

    def on_run(self, runtime: ActionContext):
        """
        Override-able method that gets called to run task logic.

        :param runtime: runtime data and API
        """
        pass

    def on_done(self, runtime: ActionContext):
        """
        Override-able method called after running tasks in reverse order.

        :param runtime: runtime data and API
        """
        pass
