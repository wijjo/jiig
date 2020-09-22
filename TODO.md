# Fixes

# Rationalize (and limit) the tasks that are inherited by tools

Jiig should probably handle all tasks not directly related to a tool's problem
domain.

To allow the `jiig` command to manipulate a tool it needs the ability to access
a tool's configuration, e.g. `init.jiig` file, and virtual environment. Tool
manipulation tasks need an option or argument that identifies a tool in a way
that its files can be located.

Perhaps only `help` should be inherited, in order to keep the tool task list
"clean". Specifically, tasks like `alias` and `venv` should probably move to the
`jiig` command and not be inherited.

# Planned Features

## Unit tests

E.g. make a `test` task in Jiig that can recognize a tool with unit tests based
on the contents of the working folder.

Create more unit tests to exercise the Jiig utility library.

Add tests to validate the tool infrastructure using a specially-designed tool
with an assortment of fake tasks.

Test code generation, virtual environment creation/management, etc..


## Documentation

Implement something like Sphinx to capture API documentation from doc strings.
This may require a virtual environment. It could be a separate Jiig build tool.
Incorporate higher level framework reference documentation from other files,
e.g. from .rst files.

Should also write a tutorial.

## Inherit and expose normally-hidden sub-tasks

By default, some Jiig sub-tasks are not inherited by tools, for example, ones
that work with tool creation virtual environment manipulation, like `create`,
`venv`, `python`, and `pip`.

Provide a mechanism for tools to explicitly inherit and expose these normally-
hidden sub-tasks. An `INHERIT_TASKS` list in the `init.jiig` file is one
possible way the overrides could be declared.

## History

Provide a `history` task, similar to `alias`, that keeps track of previous
command line arguments and allows them to be listed and retrieved. Historical
commands can be invoked as `#nn` where `nn` is an integer index that can be seen
in a history listing. Additional options and arguments can appear after the
`#nn` specifier, if they make sense.

## Output capture

### Capture output to a file.

Add a global option, e.g. `-c` to capture output in a file.

### Capture results to the clipboard.

Add a global option, e.g. '-C' to copy results to the clipboard. Perhaps add a
boolean keyword, e.g. "result", to log_message that flags a logged value as a
result. If the option is set to populate the clipboard accumulated results can
be copied with linefeed separators before successfully exiting.

## Global options

Add ability to save and use global tool options to be able to control features
like history and output capture. Tools should be able to add their own options
and hide some Jiig ones, e.g. if it doesn't want to support history or output
capture for security reasons.

## Smarter option/argument types

Look into adding custom validation and output data types. E.g. add the ability
to accept date strings that get validated and converted to a struct_time or time
stamp integer.

One possibility could be to all registration of new actions, in addition to
'store_true', etc.. E.g. a 'store_date' action could be registered with a class
that can parse, validate, and convert date strings.
