#!/usr/bin/env python3

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

import jiig.tasks
from .constants import DEFAULT_ROOT_TASK_NAME
from .task import Task, TaskGroup, TaskTree
from .tool import ToolMetadata
from .startup import tool_main


JIIGADMIN_META = ToolMetadata(
    tool_name='jiig',
    project_name='Jiig',
    description='Jiig administration tool.',
    version='0.5',
    author='Steve Cooper',
    copyright='2021-2023, Steve Cooper',
    email='steve@wijjo.com',
    url='https://github.com/wijjo/jiig',
    pip_packages=['build', 'pdoc3'],
    doc_api_packages=['jiig'],
    doc_api_packages_excluded=['jiig.internal', 'jiig.tasks'],
)

JIIGADMIN_TASK_TREE = TaskTree(
    name=DEFAULT_ROOT_TASK_NAME,
    package=jiig.tasks,
    sub_tasks=[
        TaskGroup(
            name='alias',
            sub_tasks=[
                Task(name='delete'),
                Task(name='description'),
                Task(name='list', cli_options={'expand_names': ['-e', '--expand-names']}),
                Task(name='rename'),
                Task(name='set', cli_options={'description': ['-d', '--description']}),
                Task(name='show'),
            ],
        ),
        TaskGroup(
            name='build',
            sub_tasks=[
                Task(name='sdist'),
            ],
        ),
        TaskGroup(
            name='config',
            sub_tasks=[
                Task(name='toml_to_json')
            ],
        ),
        Task(name='help', visibility=1, cli_options={'all_tasks': ['-a', '--all']}),
        TaskGroup(
            name='pdoc',
            sub_tasks=[
                Task(name='html', cli_options={'force': ['-f', '--force']}),
                Task(name='pdf', cli_options={'port': ['-p', '--port']}),
            ],
        ),
        Task(name='unittest'),
        TaskGroup(
            name='venv',
            sub_tasks=[
                Task(name='build', cli_options={'rebuild_venv': ['-r', '--rebuild']}),
                Task(name='ipython', cli_trailing='trailing_arguments'),
                Task(name='pip', cli_trailing='trailing_arguments'),
                Task(name='python', cli_trailing='trailing_arguments'),
                Task(name='run', cli_trailing='trailing_arguments'),
                Task(name='update'),
            ],
        ),
    ],
)


def jiigadmin_main():
    tool_main(meta=JIIGADMIN_META, task_tree=JIIGADMIN_TASK_TREE, is_jiig=True)
