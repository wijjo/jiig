# Planned Features

## Documentation

Implement something like Sphinx to capture API documentation from doc strings.
This may require a virtual environment. It could be a separate Jiig build tool.
Incorporate higher level framework reference documentation from other files,
e.g. from .rst files.

Should also write a tutorial.

## Aliases

An `alias` sub-task is inherited by all Jiig-based tools.

The `alias` command requires a name argument, and can accept all trailing
options and arguments. It likely needs to pre-process the command line in order
to be lenient in accepting options and arguments. It needs to support options
for deleting, overwriting, and listing existing aliases, based on scope, or not.

The alias definition is saved in `~/<tool>.alias`, probably in JSON format. It
saves aliases as a dictionary of names mapped to partial command line argument
lists. The saved alias names need to include a scope prefix, e.g. 
`<path>:<name>` to allow for resolving aliases based on location.

When processing command line arguments a pre-processing stage looks for common
global options plus trailing commands, arguments and options. The first command
argument has to be given special attention. It might be the `alias` command, an
alias invocation, or a normal command.

An `alias` command is re-parsed with special options, and with trailing 
arguments ignored.

An alias invocation is discovered by testing the first command name against the 
possible saved scoped alias names in `~/<tool>.alias`. It would need to test all
patterns implied by the folder stack, starting with the working folder and then
all of its containing folders. It prepends the discovered alias command line
fragment with the trailing command line, before handling it as a normal command.

A normal command is re-parsed with a parser generated based on the complete tool
definition, as specified by `@map_task()` decorators.

### Alias usage example

The following example uses a fictional tool called `mytool` which accepts a
message argument and x, y coordinate options (as `-x <value>` and `-y <value>`).

Here is the normal behavior of the `mytool abc` command.

```
$ mytool abc -x 5 -y 10 "hello at 5,10"
(5,10) hello at 5,10

$ mytool abc -x 0 -y 0 "hello at 0,0"
(0,0) hello at 0,0

$ mytool abc "hello at ?,?"
(?,?) hello at ?,?
```

Here is an example that saves and uses an `at510` alias.

```
$ mytool alias at510 abc -x 5 -y 10
Alias "at510" saved.

$ mytool at510 "goodbye at 5,10"
(5,10) goodbye at 5,10

$ mytool alias -l
--alias--  --arguments--
at510      ['-x', '5', '-y', '10']

$ mytool alias -d at510
Alias "at510" deleted.
```

And finally, how a scoped, i.e. local, alias might work in a folder, in a 
sub-folder, and somewhere outside the scope.

```
$ cd /home/bert/Desktop

$ mytool alias .:at510 abc -x 5 -y 10
Local alias "at510" saved for "/home/bert/Desktop".

$ mytool alias -l
--alias--                  --arguments--
/home/bert/Desktop:at510   ['-x', '5', '-y', '10']

$ cd SubFolder

$ mytool alias -l
--alias--                  --arguments--
/home/bert/Desktop:at510   ['-x', '5', '-y', '10']

$ cd /tmp

$ mytool alias -l
No aliases defined for "/tmp".
```

## Inherit and expose normally-hidden sub-tasks

By default, some Jiig sub-tasks are not inherited by tools, for example, ones
that work with tool creation virtual environment manipulation, like `create`,
`venv`, `python`, and `pip`.

Provide a mechanism for tools to explicitly inherit and expose these normally-
hidden sub-tasks. An `INHERIT_TASKS` list in the `init.jiig` file is one
possible way the overrides could be declared.
