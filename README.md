# Jiig

Jiig is a framework and tool that makes it easier to create multi-command shell
tools. Jiig tool interfaces function similar to the `git` command. See the
features below for more details.

`Tzar` (https://github.com/wijjo/tzar) is an early example of a Jiig tool.

## Features

### Multi-command

All functionality is accessed through single or multi-level sub-commands.

### Simple execution model

Jiig scripts use `jiig-run` for the "shebang" line instead of Python. This
provides the needed hook to set up and use a virtual environment, prepare the
library load path, execute the tool script to load decorated task functions and
modules, build the argparse-based command line interface, and then to parse and
run the command line.

### Declarative structure

CLI command names, text, options, and arguments are specified in `@task`
decorators attached to implementation functions in task modules. There is no
central code that needs to be updated for new sub-task commands.

Tasks are registered by declaring them in the main script or by loading modules
that contain decorated functions.

### Simple configuration

An optional `init.jiig` file can configure the following information for one or
more Jiig tools in a folder.

* LIB_FOLDERS: Library folders for access to additional modules.
* VENV_ROOT: Virtual environment root folder, if a virtual environment is
  needed. Jiig will automatically build the environment with dependencies. 
* PIP_PACKAGES: Pip package names for installing in the virtual environment. 

Paths should be relative, allowing the file to be part of a source repository.

If there is no `init.jiig` configuration file, it runs without a virtual
environment, and with a library path that provides access to both Python
Standard Library and Jiig modules.

### Auto-generated `argparse` CLI

As mentioned, the command line interface (CLI) is automatically generated based
on task function `@task` decorators. The supplied meta-data feeds into the
construction of an `argparse` CLI argument parser, including sub-parsers for 
task commands, a help system, options, and arguments.

### Dependencies and the virtual environment

Jiig itself has no external dependencies beyond Python (version 3.x).
 
Jiig-based tools depend on `jiig` and `jiig-run` being available in the path.

Tool-specific dependencies can be handled by a virtual environment by defining a
list of Pip-installed package that get automatically included when the virtual
environment is created or updated. The environment can be updated at any
time, e.g. to handle dependency changes.

### Utility functions

The Jiig library provides useful utility functions and classes for running
external commands, and for supporting other common shell command needs.

### Limited code generation

The `tool` sub-command can generate a tool project or basic script.

The `task` sub-command can generate a basic task module.

### Simple Jiig script code

The code generation is probably superfluous, because there is very little code
needed for a basic Jiig script. Here is a minimal example.

```
#!/usr/bin/env jiig-run

"""This is my program!"""

import jiig

@jiig.task()
def hello(runner):
    """a friendly greeting"""
    print('hello')

@jiig.task()
def goodbye(runner):
    """a friendly farewell"""
    print('goodbye')
```

Here is an actual demo session.

```
$ ./hello help
usage: hello [-h] [-d] [-v] [-n] TASK ...

This is my program!

positional arguments:
  TASK
    goodbye   a friendly farewell
    hello     a friendly greeting
    help      display help screen

optional arguments:
  -h, --help  show this help message and exit
  -d          enable debug mode
  -v          display additional (verbose) messages
  -n          display actions without executing them

$ ./hello goodbye
goodbye
```

The doc strings provide some command line help. The function names are used as
task names. This provides a very quick and intuitive starting point, but ongoing
development might be better served by using explicit script and task metadata.


## Aliases

Aliases allow users to capture and retrieve commonly-used partial or complete
tasks, arguments, and options. They are saved for the user as special names that
can be used instead of normal task commands.

The feature is available through the `alias` task command, and may be inherited
by any Jiig-based tool.

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


## Future documentation

There is no reference manual or user guide yet. It will definitely happen. For
now the best way to get started is this READ-ME and the Tzar project (mentioned
above) as an example.
