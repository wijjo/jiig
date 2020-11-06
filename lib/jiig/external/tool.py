"""
Jiig tool declaration support.
"""

from typing import Text
from jiig.internal.registry import register_tool
from jiig.typing import NoteDict, NotesSpec


def tool(name: Text = None,
         description: Text = None,
         notes: NotesSpec = None,
         disable_alias: bool = None,
         disable_help: bool = None,
         disable_debug: bool = None,
         disable_dry_run: bool = None,
         disable_verbose: bool = None,
         common_footnotes: NoteDict = None):
    """
    Declare tool options and metadata.

    :param name: name of tool
    :param description: description of tool
    :param notes: additional notes displayed after help body
    :param disable_alias: disable aliases if True
    :param disable_help: disable help task if True
    :param disable_debug: disable debug option if True
    :param disable_dry_run: disable dry run option if True
    :param disable_verbose: disable verbose option if True
    :param common_footnotes: common named common_footnotes for reference by options/arguments
    """
    register_tool(name=name,
                  description=description,
                  notes=notes,
                  disable_alias=disable_alias,
                  disable_help=disable_help,
                  disable_debug=disable_debug,
                  disable_dry_run=disable_dry_run,
                  disable_verbose=disable_verbose,
                  common_footnotes=common_footnotes)
