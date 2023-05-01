# Copyright (C) 2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

from .task import (
    Task,
    TaskGroup,
)

BUILTINS: dict[str, Task | TaskGroup] = {
    #: Task group for "alias" sub-commands.
    'alias': TaskGroup(
        name='alias',
        sub_tasks=[
            Task(name='delete'),
            Task(name='description'),
            Task(name='list', cli_options={'expand_names': ['-e', '--expand-names']}),
            Task(name='rename'),
            Task(name='set', cli_options={'description': ['-d', '--description']}),
            Task(name='show'),
        ],
        visibility=1,
    ),

    #: Task group for building a distribution.
    'build': TaskGroup(
        name='build',
        sub_tasks=[
            Task(name='sdist'),
        ],
        visibility=1,
    ),

    #: Task group for configuration manipulation tools.
    'config': TaskGroup(
        name='config',
        sub_tasks=[
            Task(name='toml_to_json'),
        ],
        visibility=1,
    ),

    #: Task group for generating and serving documentation.
    'doc': TaskGroup(
        name='doc',
        sub_tasks=[
            Task(name='html'),
            Task(name='markdown'),
            Task(name='pdf'),
            Task(name='server', cli_options={'port': ['-p', '--port']}),
        ],
        visibility=1,
    ),

    #: Task for "help" command.
    'help': Task(
        name='help',
        visibility=1,
        cli_options={'all_tasks': ['-a', '--all']},
    ),

    #: Task for running unit tests.
    'unittest': Task(
        name='unittest',
        visibility=1,
    ),

    #: Task group for "venv" (virtual environment) sub-commands.
    'venv': TaskGroup(
        name='venv',
        sub_tasks=[
            Task(name='build', cli_options={'rebuild_venv': ['-r', '--rebuild']}),
            Task(name='ipython', cli_trailing='trailing_arguments'),
            Task(name='pip', cli_trailing='trailing_arguments'),
            Task(name='python', cli_trailing='trailing_arguments'),
            Task(name='run', cli_trailing='trailing_arguments'),
            Task(name='update'),
        ],
        visibility=1,
    ),
}
