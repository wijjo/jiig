# Jiig

Jiig is a framework that makes it easier to create multi-command shell tools.
Jiig tool interfaces function similar to the `git` command. See the features
below for more details.

`Tzar` (https://github.com/wijjo/tzar) provides a good example of a Jiig-based 
project.

## Features

### Multi-command

All functionality is accessed through single or multi-level sub-commands.

### Declarative structure

CLI command names, text, options, and arguments are specified in `@map_task`
decorators attached to implementation functions in task modules. There is no
central code that needs to be updated when sub-commands are added.

### Simple configuration

An `init.jiig` file specifies, using Python syntax, the following:

* The tool name and description.
* The virtual environment location, and the packages to install in it.
* Where to find libraries.

Paths should be relative, allowing the file to be part of a source repository.

### Automatic task module loading

Task modules are found by searching the library folders specified in `init.jiig`
and looking for a `tasks.jiig` file in one or more folders. That file can be
empty, but indicates that the folder should have all of its contained modules
loaded at startup. The task `@map_task`-decorated functions are automatically
registered and integrated with the command line interface.

### Auto-generated `argparse` CLI

As mentioned, the command line interface (CLI) is automatically generated based
on task function `@map_task` decorators. The supplied meta-data feeds into the
construction of an `argparse` CLI argument parser, including sub-parsers for 
task commands, a help system, options, and arguments.

### Dependencies and the virtual environment

Jiig itself has no external dependencies beyond Python (version 3.x).
 
Jiig-based tools should only need Jiig as a dependency. That one dependency
could be eliminated by incorporating Jiig into the tool. One possible solution
for a source project is to include Jiig as a Git submodule.

Jiig-based commands run in an automatically generated Python virtual 
environment. Jiig tools can define a list of Pip-installed dependencies that get
automatically included when the virtual environment is created. The environment
can be regenerated at any time, e.g. to handle dependency changes. 

### Utility functions

The Jiig library provides useful utilities for running external commands, and
for supporting other common shell command needs.

### Limited code generation

The `create` sub-command supports generating tool and tool command skeletons.

Since the structure and code is kept simple, and the main script should not
require modification, copying and renaming selected files from an existing
project also works.

## Future documentation

There is no reference manual or user guide yet. It will definitely happen. For
now the best way to get started is this READ-ME and the Tzar project (mentioned
above) as an example.
