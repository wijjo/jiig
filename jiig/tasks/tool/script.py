"""Tool creation task."""

import os

import jiig
from jiig.util.template_expansion import expand_folder


@jiig.task
def script(
    runtime: jiig.Runtime,
    force: jiig.f.boolean('Force overwriting of target files.',
                          cli_flags=('-f', '--force')),
    tool_name: jiig.f.text('Tool name (default: <folder name>).',
                           cli_flags=('-T', '--tool-name')),
    tool_folder: jiig.f.filesystem_folder('Generated tool output folder.',
                                          absolute_path=True,
                                          ) = '.',
):
    """Create monolithic Jiig tool script."""
    expand_folder(
        os.path.join(runtime.tool.jiig_root_folder, 'templates/tool/script'),
        tool_folder,
        overwrite=force,
        symbols={
            'jiig_root': runtime.tool.jiig_root_folder,
            'mytool': tool_name or os.path.basename(tool_folder),
        },
    )
