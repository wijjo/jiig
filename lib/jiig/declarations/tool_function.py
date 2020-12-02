from typing import Text, Type

from jiig.registration import register_tool, RegisteredRunner
from jiig.utility.footnotes import NotesSpec, NoteDict


def tool(name: Text = None,
         description: Text = None,
         notes: NotesSpec = None,
         disable_alias: bool = None,
         disable_help: bool = None,
         disable_debug: bool = None,
         disable_dry_run: bool = None,
         disable_verbose: bool = None,
         expose_hidden_tasks: bool = None,
         footnotes: NoteDict = None,
         runner_cls: Type[RegisteredRunner] = None):
    """
    Decorator for declaring a tool function.

    :param name: name of tool
    :param description: description of tool
    :param notes: additional notes displayed after help body
    :param disable_alias: disable aliases if True
    :param disable_help: disable help task if True
    :param disable_debug: disable debug option if True
    :param disable_dry_run: disable dry run option if True
    :param disable_verbose: disable verbose option if True
    :param expose_hidden_tasks: expose normally-hidden tasks if True
    :param footnotes: common named common_footnotes for reference by options/arguments
    :param runner_cls: optional TaskRunner sub-class to use for runner creation
    """
    register_tool(name=name,
                  description=description,
                  disable_alias=disable_alias,
                  disable_help=disable_help,
                  disable_debug=disable_debug,
                  disable_dry_run=disable_dry_run,
                  disable_verbose=disable_verbose,
                  expose_hidden_tasks=expose_hidden_tasks,
                  notes=notes,
                  footnotes=footnotes,
                  runner_cls=runner_cls)
