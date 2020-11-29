"""
Jiig tool declaration support.
"""

from inspect import isfunction, signature
from typing import Text, Any, Sequence, Callable

from jiig.registry import register_tool, register_task, register_runner_factory, \
    RunnerFactoryFunction, Argument, TaskFunction, TaskFunctionsSpec, Description, \
    ArgName, ArgumentAdapter, Cardinality, OptionFlagSpec
from jiig.utility.console import abort
from jiig.utility.footnotes import NoteDict, NotesSpec
from jiig.utility.general import make_list


def runner_factory() -> Callable[[RunnerFactoryFunction], RunnerFactoryFunction]:
    """Decorator for custom runner factories."""
    def inner(function: RunnerFactoryFunction) -> RunnerFactoryFunction:
        register_runner_factory(function)
        return function
    return inner


def tool(name: Text = None,
         description: Text = None,
         notes: NotesSpec = None,
         disable_alias: bool = None,
         disable_help: bool = None,
         disable_debug: bool = None,
         disable_dry_run: bool = None,
         disable_verbose: bool = None,
         expose_hidden_tasks: bool = None,
         footnotes: NoteDict = None):
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
                  footnotes=footnotes)


def task(name: Text,
         *arguments: Argument,
         description: Description = None,
         parent: TaskFunction = None,
         notes: NotesSpec = None,
         dependencies: TaskFunctionsSpec = None,
         receive_trailing_arguments: bool = False,
         footnotes: NoteDict = None,
         hidden_task: bool = False,
         auxiliary_task: bool = False):
    """
    Decorator for declaring a task function.

    All footnotes are displayed, even if not referenced in text by "[name]" at
    the end of a string. Unreferenced ones are displayed naked, without labels.
    In effect this allows the addition of general task notes.

    :param name: task name
    :param arguments: arguments and options classes and or instances
    :param description: task description
    :param parent: task function of parent task for sub-command
    :param notes: additional notes displayed after help body
    :param dependencies: task functions of dependency tasks
    :param receive_trailing_arguments: accept extra trailing arguments (valid for
                                       top level command)
    :param footnotes: labeled footnotes that can be referenced by task, option, or
                      argument help text (see note above about unreferenced ones)
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
    """
    # Check for missing parentheses. Will not support that kind of decorator,
    # because any solution would have to accept, with no type checking, any and
    # all arguments in order to support both ways of using the decorator.
    if isfunction(name) and parent is None and dependencies is None:
        abort(f'@task decorator for function "{name.__name__}" must'
              f' have parentheses, even if empty')

    # Called after the outer function returns to provide the task function.
    def inner(task_function: TaskFunction) -> TaskFunction:
        register_task(task_function=task_function,
                      name=name,
                      parent=parent,
                      description=description,
                      notes=notes,
                      arguments=arguments,
                      dependencies=dependencies,
                      receive_trailing_arguments=receive_trailing_arguments,
                      footnotes=footnotes,
                      hidden_task=hidden_task,
                      auxiliary_task=auxiliary_task)
        return task_function

    return inner


def sub_task(parent: TaskFunction,
             name: Text,
             *arguments: Argument,
             description: Description = None,
             notes: NotesSpec = None,
             dependencies: TaskFunctionsSpec = None,
             receive_trailing_arguments: bool = False,
             footnotes: NoteDict = None,
             hidden_task: bool = False,
             auxiliary_task: bool = False):
    """
    Decorator for declaring a sub-task function.

    All footnotes are displayed, even if not referenced in text by "[name]" at
    the end of a string. Unreferenced ones are displayed naked, without labels.
    In effect this allows the addition of general task notes.

    :param parent: task function of parent task
    :param name: task name
    :param arguments: arguments and options classes and or instances
    :param description: task description
    :param notes: additional notes displayed after help body
    :param dependencies: task functions of dependency tasks
    :param receive_trailing_arguments: accept extra trailing arguments (valid for
                                       top level command)
    :param footnotes: labeled footnotes that can be referenced by task, option, or
                      argument help text (see note above about unreferenced ones)
    :param hidden_task: normally-hidden tool-management task if True
    :param auxiliary_task: used when commands like help should be listed separately
    """
    return task(name,
                *arguments,
                description=description,
                parent=parent,
                notes=notes,
                dependencies=dependencies,
                receive_trailing_arguments=receive_trailing_arguments,
                footnotes=footnotes,
                hidden_task=hidden_task,
                auxiliary_task=auxiliary_task)


def _make_argument(name: ArgName,
                   *adapters: ArgumentAdapter,
                   description: Description = None,
                   cardinality: Cardinality = None,
                   flags: OptionFlagSpec = None,
                   default_value: Any = None,
                   choices: Sequence = None,
                   is_boolean: bool = False,
                   ) -> Argument:
    # Called for fatal error.
    def _type_error(*error_parts: Any):
        parts = [f'argument "{name}" error']
        if error_parts:
            parts.extend(map(str, error_parts))
        raise TypeError(': '.join(parts))

    # Check the name.
    if not isinstance(name, str) or not name:
        _type_error('invalid name')

    # Check and adjust the description.
    if description is not None and not isinstance(description, str):
        _type_error('bad description value', description)
    final_description = description or '(no argument description)'
    if default_value:
        final_description += f' (default: {default_value})'

    # Sanity check the cardinality.
    if cardinality is not None and (isinstance(cardinality, int) or
                                    cardinality not in ('*', '+', '?')):
        _type_error('bad cardinality value', cardinality)

    # Determine final flags list, if any, and validate.
    flag_list = make_list(flags)
    if any([not isinstance(f, str) or not f.startswith('-') for f in flag_list]):
        _type_error('bad flags', flags)

    # Sanity-check adapter function signatures.
    for adapter in adapters:
        if not isfunction(adapter):
            _type_error('non-function adapter', str(adapter))
        sig = signature(adapter)
        if not sig.parameters:
            _type_error('adapter function missing value parameter', adapter.__name__)
        elif len(sig.parameters) > 1:
            _type_error('adapter function has more than one parameter', adapter.__name__)

    return Argument(name,
                    list(adapters),
                    description=final_description,
                    cardinality=cardinality,
                    flags=flag_list,
                    default_value=default_value,
                    choices=choices,
                    is_boolean=is_boolean)


def argument(name: ArgName,
             *adapters: ArgumentAdapter,
             description: Description = None,
             cardinality: Cardinality = None,
             default_value: Any = None,
             choices: Sequence = None,
             ) -> Argument:
    """
    Factory function for declaring an @task() or @sub_task() positional argument.

    :param name: argument destination name
    :param adapters: argument adapter chain for validation/conversion
    :param description: argument description
    :param cardinality: quantity specification based on argparse nargs
    :param default_value: default value for argument instance
    :param choices: restricted collection of value choices
    """
    return _make_argument(name,
                          *adapters,
                          description=description,
                          cardinality=cardinality,
                          default_value=default_value,
                          choices=choices)


def option(name: ArgName,
           flags: OptionFlagSpec,
           *adapters: ArgumentAdapter,
           description: Description = None,
           cardinality: Cardinality = None,
           default_value: Any = None,
           choices: Sequence = None,
           ) -> Argument:
    """
    Factory function for declaring an @task() or @sub_task() option argument.

    :param name: argument destination name
    :param flags: command line option flag(s)
    :param adapters: argument adapter chain for validation/conversion
    :param description: argument description
    :param cardinality: quantity specification based on argparse nargs
    :param default_value: default value for argument instance
    :param choices: restricted collection of value choices
    """
    return _make_argument(name,
                          *adapters,
                          description=description,
                          cardinality=cardinality,
                          flags=flags,
                          default_value=default_value,
                          choices=choices)


def bool_option(name: ArgName,
                flags: OptionFlagSpec,
                description: Description = None,
                ) -> Argument:
    """
    Factory function for declaring an @task() or @sub_task() boolean option.

    :param name: argument destination name
    :param flags: command line option flag(s)
    :param description: argument description
    """
    return _make_argument(name,
                          description=description,
                          flags=flags,
                          is_boolean=True)
