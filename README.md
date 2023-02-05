# Jiig

Jiig is a framework and tool kit for simplifying the creation of shell tools and
potentially other kinds of programs.


## Advantages

### Data-driven user interface

### Type-safety

### Clean business logic

### Easy interface changes

### Task structure

### Modular user interface drivers


## Program structure

* A user-selectable driver interprets metadata to produce a user interface.
* Decorated @task functions.
    * Declares a function that implements a "task", which provides a type-safe
      function that can be invoked by any user interface implementation. 
    * Task function arguments are annotated by field declarations which can
      specify documentation, validation, and type conversion.
* Tool configuration file, "jiig.yaml" specifies the following:
    * Tool metadata, including description, author, copyright, etc..
    * Task tree maps registered task functions to a user interface, e.g. a text- 
      based command line interface. 

Task function code can be focused on pure "business" logic, since field data
validation and type conversion is handled externally. For example, an argument 
could require an existing file path.
-

## User interface

The initial Jiig release supports argparse-based command line interfaces (CLIs).
But user interfaces (UIs) are modular, and are implemented by drivers that convert
field data and UI-specific hints into a concrete user interface.

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

The framework is designed to make it easy to build from scratch, i.e. without
needing a code generator, aided by a fully-typed API.

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

The tool configuration file, "jiig.yaml", maps the full task structure to a user
interface.

### Main tool script and execution model

Jiig tool scripts can use `jiig` as the top "shebang" command line. This causes
Jiig to become the script interpreter. Such tool scripts run Python indirectly.
The advantage is that Jiig can provide a fully-initialized virtual environment,
plus a library load path that allows access to Jiig and tool modules.

### Dependencies and the virtual environment

Jiig and Jiig-based tools always run from a virtual environment with all
dependencies satisfied. Both Jiig and the tool can specify Pip package
requirements for the virtual environment.

Jiig-based tools that use Jiig as the script interpreter rely on `jiig` being
available in the system execution path.

### Utility library

Jiig provides a utility library ("jiig.util") with a rich variety of useful
functions and classes, including external command execution, a variety of text
manipulations, command line aliases, filesystem access, logging, and more.

## Documentation and type inspection

There is no API documentation yet, but abundant doc strings and type hints
assist while programming in an IDE.

## Aliases

Aliases allow users to capture and retrieve commonly-used partial or complete
tasks, arguments, and options. They are saved for the user as special names that
can be substitute for normal task commands.

The feature is available through the `alias` task command, and the functionality
may be inherited by any Jiig-based tool.

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

You can base a new project on examples provided with this library.
