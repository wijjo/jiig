# Planned Features

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
