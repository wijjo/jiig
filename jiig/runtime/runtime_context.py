"""
Runtime execution and symbol expansion context.
"""

import subprocess
from typing import TypeVar, Sequence, Union, ContextManager

from jiig.util.action_context import ActionContext
from jiig.util.git import repo_name_from_url

from .options import Options
from .runtime_options import RuntimeOptions
from .provisioning_script import ProvisioningScript

T_provisioning_script = TypeVar('T_provisioning_script', bound=ProvisioningScript)


class RuntimeContext(ActionContext):
    """Nestable runtime context for context-sensitive symbol expansion."""

    def __init__(self):
        """Construct runtime context."""
        self.options = RuntimeOptions(Options.debug,
                                      Options.dry_run,
                                      Options.verbose,
                                      Options.pause)
        super().__init__()

    def run(self,
            command: Union[str, Sequence],
            predicate: str = None,
            capture: bool = False,
            unchecked: bool = False,
            ignore_dry_run: bool = False,
            messages: dict = None,
            ) -> subprocess.CompletedProcess:
        return self.run_command(
            command,
            predicate=predicate,
            capture=capture,
            unchecked=unchecked,
            dry_run=self.options.dry_run and not ignore_dry_run,
            messages=messages,
        )

    def script(self,
               messages: dict = None,
               unchecked: bool = False,
               run_by_root: bool = False,
               script_class: T_provisioning_script = None,
               ) -> ContextManager[T_provisioning_script]:
        if script_class is None:
            script_class = ProvisioningScript
        return super().script(messages=messages,
                              unchecked=unchecked,
                              run_by_root=run_by_root,
                              script_class=script_class)

    def get_repo_name(self) -> str:
        return repo_name_from_url(self.pipe('git config --get remote.origin.url'))
