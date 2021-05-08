# Jiig

Jiig is a framework and tool for creating multi-command shell tools. Jiig-based
tool interfaces resemble the `git` command structure. It has multi-level
sub-commands, options, and arguments, along with integrated "help" command.

`Tzar` (https://github.com/wijjo/tzar) is an early example of a Jiig-based tool
that is written by the same author.

## Features

### Simple and flexible command line interface

All functionality is accessible through a command line interface, i.e. "CLI",
that supports a hierarchy of sub-commands. In Jiig terminology sub-commands are
called "tasks". Tasks can have flagged options and positional arguments.

Help is provided by a multi-level "help" sub-command.

Complex full or partial command lines may be saved and retrieved through an
"alias" facility and sub-command that can be inherited by any tool.

### Declarative `argparse` CLI definitions

The command line interface driver is designed to support multiple
implementations, but for now only the standard Python "argparse" library is
supported.

A Tool sub-class defines the top level of meta-data and tasks. Tasks are pulled
in by referencing Task sub-classes or modules in lists declared in Tool and Task
classes.

### Modular structure

Task modules are ordinary modules, except they need to have a specially named
Task sub-class called "TaskClass". Which tasks get integrated into the tool is
solely determined by whether or not they are referenced in active task lists.

### Main tool script and execution model

Jiig tool scripts use `jiig-run` for the top "shebang" comment line. This line
defines the shell executable program for the script. So tool scripts do not run
Python directly. The final interpreter is pulled in by Jiig and configured to
provide the correct runtime environment, including the library path.

The indirect execution structure also allows `jiig-run` to set up and use a
virtual environment, if the tool is configured for one.

The tool main script declares or imports the primary Tool class, which needs to
be called "ToolClass".

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

The `tool` sub-command can generate a tool project or basic tool script.

The `task` sub-command can generate a basic task module.

## Documentation amd type inspection

There is no API documentation yet, but all or most significant modules, classes,
and functions have useful doc strings.

The programming interface is also very well typed. So an IDE like PyCharm or
VS-Code with appropriate plug-ins can provide a lot of assistance.

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


## Getting started

Use the "jiig tool project" or "jiig tool script" command to create either a
multi-folder/multi-file project or a stand-alone script. Follow the comments and
generated code for hints about how to proceed.

The "jiig task create" command can add a new task to an existing project, but it
needs to be given the task library folder.

Use the "help" task get more information on how to use the Jiig command line
interface.
