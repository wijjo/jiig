"""
Tool execution initialization.
"""

from jiig.task_runner import RunnerData, TaskRunner
from .. import registry
from jiig.utility.console import abort
from jiig.utility.init_file import ParamData

from .parameters_initializer import ParameterData
from .tool_initializer import ToolData
from .arguments_initializer import ArgumentData


def initialize(param_data: ParameterData,
               tool_data: ToolData,
               arg_data: ArgumentData,
               ):
    """
    Initialize tool execution.

    :param param_data: data from command-line pre-processing
    :param tool_data: data from tool loading and initialization
    :param arg_data: data from final command line argument parsing
    """
    # Bundle the data shared with tasks through the task runner.
    runner_data = RunnerData(arg_data.data,
                             arg_data.trailing_arguments,
                             tool_data.help_formatters,
                             ParamData(
                                 ALIASES_PATH=param_data.aliases_path,
                                 DEBUG=param_data.debug,
                                 DRY_RUN=param_data.dry_run,
                                 FULL_NAME_SEPARATOR=param_data.full_name_separator,
                                 JIIG_ROOT=param_data.jiig_root,
                                 JIIG_TASK_TEMPLATE=param_data.jiig_task_template,
                                 JIIG_TEMPLATES_FOLDER=param_data.jiig_templates_folder,
                                 LIB_FOLDERS=param_data.library_folders,
                                 PIP_PACKAGES=param_data.pip_packages,
                                 TEST_ROOT=param_data.test_root,
                                 TOOL_DESCRIPTION=tool_data.description,
                                 TOOL_NAME=tool_data.name,
                                 TOOL_TEMPLATES_FOLDER=param_data.tool_templates_folder,
                                 VENV_ROOT=param_data.venv_root,
                                 VERBOSE=param_data.verbose,
                             ))

    # Run the tool to invoke the specified task.
    runner_factory = registry.get_runner_factory()
    if runner_factory:
        runner = runner_factory(runner_data)
    else:
        runner = TaskRunner(runner_data)
    try:
        # Execute task dependencies first.
        for dependency_task in arg_data.registered_task.execution_tasks:
            dependency_task.task_function(runner)
        # Then execute the primary task.
        arg_data.registered_task.task_function(runner)
    except RuntimeError as exc:
        abort(f'{exc.__class__.__name__}("{exc}")', runner_data.args)
    except KeyboardInterrupt:
        print('')
