# Improvements

* [ ] Add task function support for delayed clean-up?
    * [X] Support `runtime.when_done(function)`?
    * [ ] Or add chained decorator, similar to @property getter/setter pairs.
    * [ ] Test it.

* [ ] Automatic file backups, e.g. for ~/.jiig.
    * [ ] Accept "backup discipline" as optional argument.
    * [ ] Define backup discipline protocol (as a class) for future expansion.
    * [ ] Implement backup discipline for single backup copy, possibly with
          option to not overwrite existing same day backup.
    * [ ] Switch catalog save to use stream.open_input_file() with above backup
          single backup copy discipline.
    * [ ] Could also not bother building backup into open_input_file(), and just
          handle it separately.

# Fixes

## Improve util.python.import_module_path()'s error handling.

Decide whether or not to raise exceptions, etc.

## Rebuild virtual environment fails.

`jiig venv build -r` fails.

# Planned Features

## Unit tests

E.g. make a `test` task in Jiig that can recognize a tool with unit tests based
on the contents of the working folder.

Create more unit tests to exercise the Jiig utility library.

Add tests to validate the tool infrastructure using a specially-designed tool
with an assortment of fake tasks.

Test virtual environment creation/management, etc..


## Documentation

Write a tutorial.

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
