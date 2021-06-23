"""
Runner provides data and an API to task call-back functions..
"""

from contextlib import contextmanager
from typing import Text, Iterator

from jiig.registry import RegisteredContext
from jiig.util.alias_catalog import AliasCatalog, open_alias_catalog

from .runtime_options import Options
from .runtime_tool import RuntimeTool


class RuntimeHelpGenerator:
    """Abstract base class implemented by a driver to generate on-demand help output."""
    def generate_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        raise NotImplementedError


class Runtime(RegisteredContext):
    """
    Application Runtime class.

    This is the top level context presented to task call-back methods.

    Can also use as a base for registered custom runtime classes.

    Self-registers sub-classes to the context registry.

    The class declaration accepts no keyword arguments.
    """

    def __init__(self,
                 tool: RuntimeTool,
                 help_generator: RuntimeHelpGenerator,
                 data: object,
                 **kwargs,
                 ):
        """
        Construct root runtime context.

        Passed to Task call-back methods to provide a runtime API and text
        symbol expansion.

        :param tool: tool data
        :param help_generator: on-demand help generator
        :param data: parsed command line argument data
        :param kwargs: initial symbols
        """
        self.tool = tool
        self.help_generator = help_generator
        self.data = data
        self.options = Options
        super().__init__(
            None,
            aliases_path=tool.aliases_path,
            author=tool.author,
            build_folder=tool.build_folder,
            copyright=tool.copyright,
            description=tool.description,
            doc_folder=tool.doc_folder,
            jiig_library_folder=tool.jiig_library_folder,
            jiig_root_folder=tool.jiig_root_folder,
            pip_packages=tool.pip_packages,
            project_name=tool.project_name,
            sub_task_label=tool.sub_task_label,
            tool_name=tool.name,
            tool_root_folder=tool.tool_root_folder,
            top_task_label=tool.top_task_label,
            venv_folder=tool.venv_folder,
            version=tool.version,
            **kwargs,
        )

    @contextmanager
    def open_alias_catalog(self) -> Iterator[AliasCatalog]:
        """
        Open alias catalog.

        For use in a `with` block to automatically close the catalog.

        :return: catalog
        """
        with open_alias_catalog(self.tool.name, self.tool.aliases_path) as catalog:
            yield catalog

    def provide_help(self, *names: Text, show_hidden: bool = False):
        """
        Provide help output.

        :param names: name parts (task name stack)
        :param show_hidden: show hidden task help if True
        """
        self.help_generator.generate_help(*names, show_hidden=show_hidden)
