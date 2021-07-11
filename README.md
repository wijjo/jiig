# Jiig

Jiig is a framework and tool kit for simplifying the creation of shell tools and
various other kinds of programs.


## Advantages

### Data-driven user interface

### Type-safety

### Clean business logic

### Easy interface changes

### Task structure

### Modular user interface drivers


## Program structure

* User-selected driver to interpret metadata as a user interface.
* Tool definition, either as a special tool script or a Tool object.
    * Tool metadata.
    * Root (top level) Task class reference.
* Task classes (self-registering).
    * Task class annotated fields.
    * Task class call-back action methods.
    * Optional child sub-task references.

1. Task classes, their metadata and methods.
2. Field annotations within task classes and metadata parameters.
3. A selected driver that interprets task and field metadata to drive a running
   program and user interface.

Business logic coexists with task and field metadata as task class methods. The
business logic can remain pure because field data validation and type conversion
is handled externally.

But when fields and business logic do need to change in concert they are likely
found in the same file, the same class, and probably the same editor screen.


## User interface

The initial release supports argparse-based command line interfaces (CLIs). But
user interfaces (UIs) are modular, and implemented by drivers that convert field
data and UI-specific hints into the concrete user interface.

It will be possible in the future to extend field hints and add drivers to
support UI alternatives like the following.

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

It includes some code generation capability to help get started quickly. But the
framework is designed to make it easy to build from scratch, i.e. without
needing generated code.

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

Jiig tool scripts can use `jiig` as the top "shebang" command line. In this case
Jiig becomes the script interpreter. Such tool scripts do not run Python
directly. The final Python interpreter is pulled in by Jiig and configured to
provide the correct runtime environment, including the library path.

The main tool script can declare tool/project meta-data and task functions using
the @task decorator.

### Dependencies and the virtual environment

Jiig itself has no external dependencies beyond Python (version 3.x).

Jiig-based tools depend on `jiig` being available in the path.

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
