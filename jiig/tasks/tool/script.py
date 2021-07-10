"""Tool creation task."""

import os

import jiig
from jiig.util.template_expansion import expand_folder


@jiig.task(
    cli={
        'options': {
            'force': ('-f', '--force'),
            'tool_name': ('-T', '--tool-name'),
        }
    }
)
def script(
    runtime: jiig.Runtime,
    force: jiig.f.boolean(),
    tool_name: jiig.f.text(),
    tool_folder: jiig.f.filesystem_folder(absolute_path=True) = '.',
):
    """

    Create monolithic Jiig tool script.

    :param runtime: Jiig runtime API.
    :param force: Force overwriting of target files.
    :param tool_name: Tool name (default: <folder name>).
    :param tool_folder: Generated tool output folder.
    """
    expand_folder(
        os.path.join(runtime.tool.jiig_root_folder, 'templates/tool/script'),
        tool_folder,
        overwrite=force,
        symbols={
            'jiig_root': runtime.tool.jiig_root_folder,
            'mytool': tool_name or os.path.basename(tool_folder),
        },
    )
