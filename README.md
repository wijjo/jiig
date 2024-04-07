# Jiig

Jiig is a framework and tool kit for simple creation of shell tools and
potentially other kinds of programs. It can be installed like any other Pip
package. But it also can be easily used directly from downloaded source code.
I.e. it does not require installation.


## Type-safety and documentation everywhere

All Jiig-provided classes, methods, functions, and modules are fully annotated
with type hints. Task function parameters (see below) also resolve to specific
types.

All Jiig components are fully documented.

IDEs, like PyCharm or VSCode with Python extensions, can provide code completion
prompts, type mismatch warnings, pop-up documentation, etc..


## Task functions

Tasks are functions with annotated parameters that provide an API that can be
invoked by the user interface, e.g. to execute CLI commands.

Task functions tend to have clean business logic for the following reasons.

* They have no insight into how they are mapped into a user interface.
* Function parameters are validated and converted to a target type as required.

Task function implementations can concentrate on core business logic without
needing to deal with "plumbing".


## Application and user interface configuration

Application configurations can use one of the following formats:

* TOML - a friendly INI-like format with comments and complex data support.
* JSON - a simple and familiar dictionary-like format.
* Python objects - use various Jiig-supplied Python configuration classes. 

TOML is a built-in Python-supported configuration format that resembles Windows
".ini" files. It adds features like comments and support for some more complex
data structures. The `examples/bin/extool-jiigrun` script demonstrates a TOML format
configuration.

JSON is a simple format that is familiar to Web developers in particular. It is
fussier than TOML. Comma separators must be between successive elements, but 
must not be placed after the last element of a list or dictionary. Also,
comments are not supported. One advantage is that the task hierarchy is easier 
to understand, compared to the TOML equivalent. The 
`jiig utility config_to_json` command can convert a TOML configuration file to
JSON. It also works with `jiigrun` scripts, because it knows how to skip to the
first "{" line.

Configuration format is a personal choice. TOML is considered the Jiig default
format.

A pure Python configuration tends to be a little more verbose. The 
`examples/bin/extool-python` script demonstrates a pure Python configuration. 

The user interface (UI) is also configured as part of the application
configuration. UI configurations map task functions to UI elements, like command
line sub-commands, options, and arguments.


## Modular user interface drivers

A user-selectable driver interprets metadata to produce the user interface.
Currently, the only driver produces command line (CLI) programs based on the
"argparse" command line argument parser.

Future drivers might produce ReST interfaces, simple graphical (GUI)
applications, etc..


## The "jiigrun" interpreter

Calling "jiigrun" an interpreter is an overstatement. But it is intended for use
as a shell script "shebang" line interpreter. Used this way, it simplifies a few
things.

* Script contents is the application TOML configuration, which "jiigrun"
  automatically loads and validates.
* It supports using Jiig from a source installation by adjusting the Python
  library load path so that Jiig packages may be imported from the source tree.
* It automatically creates and maintains a virtual environment specifically for
  the application.


## User interface

The initial Jiig release supports argparse-based command line interfaces (CLIs).
But user interfaces (UIs) are modular, and are implemented by drivers that
convert field data and UI-specific configuration information into a concrete
user interface.

Future drivers could support UI alternatives like the following:

* ReST API based on tasks, fields, and ReST-specific hints.
* Simple dialog-based GUIs that map tasks and fields to windows and controls,
  e.g. using TK, QT, Windows, Mac, etc..
* Simple task/field-based Web interface.
* CLI libraries other than argparse, possibly including a new stand-alone Jiig
  CLI library.

It promotes an approach where user interface definition is primarily data-driven
and maintains a clean separation from core "business" logic.

`Tzar` (https://github.com/wijjo/tzar), also created by the Jiig author, is an
early Jiig-based tool example.


## Command line interface (CLI) driver

The CLI driver produces a command line application. It supports a hierarchy of
sub-commands. In Jiig terminology sub-commands are mapped to "tasks". The CLI
configuration can specify flagged options, positional arguments, and other
parsing options for command-mapped tasks.

Help is provided by a multi-level "help" sub-command.


## Jiig virtual environments

By default, Jiig and Jiig-based tools run from a virtual environment with all
dependencies satisfied. Both Jiig and the tool can specify Pip package
requirements for the virtual environment.

Jiig-based tools that use `jiigrun` as the script interpreter only rely on that
command being available in the system execution path.


## Utility library

Jiig supplies a utility library ("jiig.util") with a rich variety of useful
functions and classes. Capabilities include external command execution, a
variety of text manipulations, alias management, filesystem access, and logging.

## Aliases

Aliases allow users to capture and retrieve commonly-used partial or complete
commands, arguments, and options. They are saved for the user as special names that
can be substitute for normal commands.

The feature is available through the `alias` sub-command. The functionality may
be inherited by any Jiig-based tool.

### Alias names

Alias names, as specified on the command line, always start with '/' or '.'. The
name prefix determines the effective "scope" of the alias.

### Global aliases

Global aliases start with '/', and may be used anywhere.

#### Global alias example

```
$ mytool alias set /global mytask -x 1
Alias "/global" saved.

$ cd /the/location

$ mytool /global
(output of "mytool mytask -x 1")

$ cd /somewhere/else

$ mytool /myglobal
(output of "mytool mytask -x 1")
```

### Local aliases

Local alias names start with '.'. An alias defined with a single dot prefix may
only be easily used in the location where it was explicitly defined.

Local alias names may also start with '..'. In this case it specifies an alias
that applies to the the working folder's parent folder.

Note that the saved alias name includes the full path to support scoping.

#### Local alias example

```
$ cd /the/location

$ mytool alias set ..mylocal mytask -x 1
Alias "/the/location/mylocal" saved.

$ mytool .mylocal
(output of "mytool mytask -x 1")

$ cd sub1

$ mytool ..mylocal
(output of "mytool mytask -x 1")

$ cd /somewhere/else

$ mytool .mylocal
Alias "/somewhere/else/mylocal" not found.
```

### Alias internals

Saved alias names include the scope as a fully-resolved path. For example, if
alias `.c1` is saved from folder `/a/b/c` it is saved with the full alias name
`/a/b/c/c1`. Global alias names, or any name beginning with `/` are unchanged.
`.`, `..`, and `~` are merely convenient abbreviations for the full paths that
are substituted and used internally.


## Getting started

You can base a new project on examples provided by the Jiig project.

The instructions below outline the most common steps for a new application.

### jiigrun-based application creation

This describes the most common (simplest) application structure, with an inline
TOML configuration and a script that uses "jiigrun" as the interpreter.

#### Create a tasks package.

* Implement modules with @task functions for the various supported application
  actions.
* Declare all function parameters as Jiig fields for type validation,
  conversion, and documentation.

Below is an `extool` example task module, `calc.py`.

```python
"""Sample Jiig task module."""

from jiig.task import task
from jiig.runtime import Runtime
from jiig import fields


@task
def calc(
    runtime: Runtime,
    blocks: fields.text(repeat=(1, None)),
):
    """
    evaluate formula using Python interpreter

    Args:
        runtime: jiig runtime api
        blocks: formula block(s) to evaluate
    """
    try:
        result = eval(' '.join(blocks))
        runtime.message(f'The result is {result}.')
    except Exception as exc:
        runtime.abort(f'Formula error: {exc}')
```

#### Create an application script.

* Make "jiigrun" the script "shebang" interpreter.
* Write the application/UI configuration as inline TOML data, including:
   * Tool metadata, including description, author, copyright, etc..
   * Task tree maps registered task functions to a user interface, e.g. a  
     text-based command line interface. 

The code below is taken from `examples/extool/bin/extool-jiigrun`.

```toml
#!/usr/bin/env jiigrun

[tool]
name = "extool"
project = "Extool"
description = "extool Jiig example tool script"
version = "0.1"
author = "Extool Author"
copyright = "2023, Extool Author"
# pip_packages = ["package1", "package2"]

[tasks.calc]

[tasks.case]
cli_options = {lower = ["-l", "--lower"], upper = ["-u", "--upper"]}

[tasks.words]

[tasks.time.sub_tasks.now]
cli_options = {format = ["-f", "--format"]}

[tasks.time.sub_tasks.month]
cli_options = {date = ["-d", "--date"]}

[tasks.time.sub_tasks.year]
cli_options = {year = ["-y", "--year"]}
```

### Pure Python Jiig tool

The code below demonstrates a pure Python Jiig tool script. It is taken from
`examples/extool/bin/extool-python`, but has been simplified for readability.

```python
#!/usr/bin/env python3

from jiig.task import Task, TaskGroup, TaskTree
from jiig.tool import ToolMetadata
from jiig.startup import tool_main

def main():
    tool_main(
        meta=ToolMetadata(
            'extool',
            project_name='Extool',
            description='extool Jiig example tool script',
            author='Extool Author',
            copyright='Copyright (C) 2023, Extool Author',
            pip_packages=[],
        ),
        task_tree=TaskTree(
            sub_tasks=[
                Task(name='calc'),
                Task(name='case',
                     cli_options={'lower': ["-l", "--lower"],
                                  'upper': ["-u", "--upper"]}),
                Task(name='words'),
                TaskGroup(
                    name='time',
                    sub_tasks=[
                        Task(name='month',
                             cli_options={'date': ['-d', '--date']}),
                        Task(name='now',
                             cli_options={'format': ['-f', '--format']}),
                        Task(name='year',
                             cli_options={'year': ['-y', '--year']}),
                    ],
                )
            ],
        ),
        script_path=__file__,
    )

if __name__ == '__main__':
    main()
```

With this example the user is completely responsible for making sure Jiig is
available, and for adding `extool` to the Python library load path. Here is a
sample shell session that takes care of those requirements.

Note that `~/test/extool` has a complete copy of the `extool` example source,
including the `extool.tasks` package.

```
$ cd ~/test/extool

$ python3 -m venv venv

$ source venv/bin/activate

$ pip install jiig
...
Installing collected packages: jiig
Successfully installed jiig-0.5

$ PYTHONPATH=. bin/extool-python case abcd                                                                                                        ─╯
ABCD
```
