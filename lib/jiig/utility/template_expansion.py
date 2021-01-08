"""
Template expansion utilities.

Also supports a _template.json file, which can configure different kinds of
template expansion. A sample is shown below. Note that Python string template
symbol expansion will be applied to _template.json files.

```json
{
  "templates": [
    {
      "path": "path/to/input1.txt",
      "output_path": "path/to/$output_name.txt",
      "expansion": "word",
      "executable": false
    },
    ...
  ]
}
```

Note that $<symbol> expansion is supported within the _template.json file.

The "path" property is the relative input template file path.

The optional "output_path" property establishes a non-default relative output
path. By default "output_path" is the same as "path".

The optional "expansion" property can be "template", "word", or "copy". The
default expansion is "word".

The optional "executable" property results in executable permissions on the
output file. It defaults to False.

The default "template" expansion provides conventional Python string template
expansion. It is the same as the expansion that is automatically applied to
files with ".template*" extensions.

"Word" expansion performs regular expression symbol substitution on the input
text, but the compiled regular expressions surround symbol names with word
delimiters. It allows template files to retain conventional syntax, while making
it a bit less likely for accidental substitutions to happen. "Word" expansion
may only be specified through the _template.json configuration file.
"""

import os
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from string import Template
from typing import Text, Dict, Tuple, List, Optional, Sequence

from . import options
from .console import abort, log_topic, TopicLogger, log_block_begin, log_block_end, \
    log_error, log_warning, log_message
from .filesystem import check_file_exists, short_path, create_folder, copy_file, make_relative_path
from .general import format_message_block, format_exception
from .stream import open_text_source, read_json_source

TEMPLATE_FOLDER_SYMBOL_REGEX = re.compile(r'\(=(\w+)=\)')

TEMPLATE_JSON = '_template.json'
TEMPLATE_EXTENSION = '.template'
TEMPLATE_EXTENSION_EXE = '.template_exe'
TEMPLATE_EXTENSION_DOT = '.template_dot'
TEMPLATE_EXTENSIONS_ALL = [TEMPLATE_EXTENSION, TEMPLATE_EXTENSION_EXE, TEMPLATE_EXTENSION_DOT]


# === Private interface.


class _ExpansionError(Exception):
    pass


@dataclass
class _ConfigExpansionItem:
    # Data directly extracted and scrubbed from configuration for an expansion
    path: Text
    output_path: Text
    expansion: Text
    executable: bool


class _TemplateExpansionSpec:

    def __init__(self,
                 output_path: Text,
                 expansion: Text,
                 executable: bool,
                 ):
        self.output_path = output_path
        self.expansion = expansion
        self.executable = executable


def _get_template_folder_expansion_specs_by_path(template_folder: Text,
                                                 symbols: Dict,
                                                 ) -> Dict[Text, _TemplateExpansionSpec]:
    config_path = os.path.join(template_folder, TEMPLATE_JSON)
    expansion_specs_by_path: Dict[Text, _TemplateExpansionSpec] = {}
    for config_expansion in _get_configuration_expansions(config_path, symbols):
        expansion_spec = _TemplateExpansionSpec(config_expansion.output_path,
                                                config_expansion.expansion,
                                                config_expansion.executable)
        expansion_specs_by_path[config_expansion.path] = expansion_spec
    return expansion_specs_by_path


def _read_configuration_json(config_path: Text, symbols: Dict) -> object:
    if not os.path.isfile(config_path):
        return {}
    with open_text_source(file=config_path, check=True) as text_stream:
        raw_text = text_stream.read()
        expanded_text = _expand_python_template_text(raw_text, symbols)
        return read_json_source(text=expanded_text, check=True)


def _get_configuration_expansions(config_path: Text,
                                  symbols: Dict,
                                  ) -> List[_ConfigExpansionItem]:
    if not os.path.exists(config_path):
        return []
    expansion_items: List[_ConfigExpansionItem] = []
    with log_topic(f'"{config_path}" issues', delayed=True) as topic:
        config_json = _read_configuration_json(config_path, symbols)
        config_templates = config_json.get('templates')
        if config_templates:
            if isinstance(config_templates, list):
                expansions: Dict[Text, _TemplateExpansionSpec] = {}
                for item_num, template_dict in enumerate(config_templates, start=1):
                    sub_logger = topic.sub_topic(f'"templates" item #{item_num}')
                    if not isinstance(template_dict, dict):
                        sub_logger.error('not a dictionary')
                        continue
                    path = template_dict.get('path')
                    if not path:
                        sub_logger.error('no "path" element')
                        continue
                    if path in expansions:
                        sub_logger.error(f'path "{path}" is repeated')
                        continue
                    output_path = template_dict.get('output_path', path)
                    output_path = _expand_template_path(output_path, topic, symbols=symbols)
                    if not output_path:
                        output_path = path
                    expansion = template_dict.get('expansion')
                    if expansion and expansion not in ALL_EXPANSIONS:
                        sub_logger.error(f' bad "expansion" value "{expansion}"')
                        # `issue_once_tag` makes the message appear only once.
                        sub_logger.message(
                            f'allowed expansions are {ALL_EXPANSIONS}',
                            issue_once_tag='ALLOWED_EXPANSIONS')
                        expansion = DEFAULT_EXPANSION
                    executable = template_dict.get('executable', False)
                    if not isinstance(executable, bool):
                        sub_logger.error(f'bad non-boolean "executable" value "{executable}"')
                        executable = False
                    expansion_items.append(
                        _ConfigExpansionItem(path, output_path, expansion, executable))
            else:
                topic.error('"templates" element is not a list')
        else:
            topic.warning('no "templates" list is present')
        # Any errors?
        if topic.get_counts()[0]:
            return []
    return expansion_items


def _set_permissions(target_path: Text, executable: bool = False):
    if executable:
        chmod_command = f'chmod +x {target_path}'
        log_message('Set executable permission.', target=short_path(target_path))
        if not options.DRY_RUN:
            try:
                os.system(chmod_command)
            except (IOError, OSError) as exc_write_error:
                abort('Failed to set executable permission.',
                      target=short_path(target_path),
                      exception=exc_write_error)
        else:
            log_message(chmod_command)


def _simple_copy(source_path: Text,
                 target_path: Text,
                 overwrite: bool = False,
                 ):
    create_folder(os.path.dirname(target_path))
    copy_file(source_path, target_path, overwrite=overwrite)


def _expand_python_template(source_path: Text, target_path: Text, symbols: Dict):
    with open_text_source(file=source_path) as input_stream:
        create_folder(os.path.dirname(target_path))
        if not options.DRY_RUN:
            with open(target_path, 'w', encoding='utf-8') as output_stream:
                output_text = _expand_python_template_text(input_stream.read(), symbols)
                output_stream.write(output_text)


def _expand_regular_expressions(source_path: Text,
                                target_path: Text,
                                substitutions: List[Tuple[re.Pattern, Text]]):
    with open_text_source(file=source_path) as input_stream:
        create_folder(os.path.dirname(target_path))
        if not options.DRY_RUN:
            with open(target_path, 'w', encoding='utf-8') as output_stream:
                output_text = input_stream.read()
                for pattern, replacement in substitutions:
                    output_text = pattern.sub(replacement, output_text)
                output_stream.write(output_text)


def _build_word_substitution_list(symbols: Dict = None) -> List[Tuple[re.Pattern, Text]]:
    if not symbols:
        return []
    return [(re.compile(fr'\b{word}\b'), repl) for word, repl in symbols.items()]


def _expand_template_path(source_path: Text,
                          topic: TopicLogger,
                          symbols: Dict = None,
                          ) -> Text:
    if not symbols:
        return source_path
    name_parts = []
    pos = 0
    for match in TEMPLATE_FOLDER_SYMBOL_REGEX.finditer(source_path):
        name = match.group(1)
        start_pos, end_pos = match.span()
        if start_pos > pos:
            name_parts.append(source_path[pos:start_pos])
        if name in symbols:
            name_parts.append(symbols[name])
        else:
            topic.error(f'Symbol "{name}" not found for path template "{source_path}".')
            name_parts.append(source_path[start_pos:end_pos])
        pos = end_pos
    if pos < len(source_path):
        name_parts.append(source_path[pos:])
    expanded_name = ''.join(name_parts)
    return expanded_name


class _TemplateExpander:
    def __init__(self,
                 source_root: Text,
                 overwrite: bool = False,
                 symbols: Dict = None,
                 ):
        if not os.path.exists(source_root):
            abort(f'Source template folder does not exist.',
                  source_root)
        if not os.path.isdir(source_root):
            abort(f'Source template folder path exists, but is not a folder.',
                  source_root)
        self.source_root = source_root
        self.overwrite = overwrite
        self.symbols = symbols or {}
        self.substitutions: Optional[List[Tuple[re.Pattern, Text]]] = None
        self.expansion_specs_by_path = _get_template_folder_expansion_specs_by_path(
            source_root, symbols)
        # Skipped file paths hard-coded for now to skip the configuration file.
        self.skipped_paths = [TEMPLATE_JSON]

    def expand(self,
               target_root: Text,
               sub_folder: Text = None,
               excludes: Sequence[Text] = None,
               includes: Sequence[Text] = None,
               ):
        if os.path.exists(target_root) and not os.path.isdir(target_root):
            abort(f'Target folder path exists, but is not a folder.',
                  target_root)
        if sub_folder is None:
            source_folder = self.source_root
            target_folder = target_root
        else:
            source_folder = os.path.join(self.source_root, sub_folder)
            target_folder = os.path.join(target_root, sub_folder)
        log_block_begin(1, 'Expanding templates')
        log_message('Folders:', source=source_folder, target=target_folder)
        failed = False
        for visit_folder, visit_sub_folders, visit_file_names in os.walk(source_folder):
            relative_folder = make_relative_path(visit_folder, source_folder)
            log_block_begin(2, f'Folder {relative_folder}')
            for file_name in visit_file_names:
                relative_path = os.path.join(relative_folder, file_name)
                if relative_path in self.skipped_paths:
                    continue
                if includes is not None:
                    for include_pattern in includes:
                        if fnmatch(relative_path, include_pattern):
                            break
                    else:
                        continue
                if excludes is not None:
                    for exclude_pattern in excludes:
                        if not fnmatch(relative_path, exclude_pattern):
                            continue
                try:
                    self.expand_file(relative_path, target_root)
                except _ExpansionError as exc:
                    log_error(str(exc))
                    failed = True
            log_block_end(2)
        log_block_end(1)
        if failed:
            abort('Template expansion failed.')

    def expand_file(self, relative_path: Text, target_root: Text):

        expansion_spec = self._get_expansion_spec(relative_path)

        # Compile word regular expression substitutions if first word expansion.
        if expansion_spec.expansion == WORD_EXPANSION and self.substitutions is None:
            self.substitutions = _build_word_substitution_list(self.symbols)

        source_path = os.path.join(self.source_root, relative_path)
        target_path = os.path.join(target_root, expansion_spec.output_path)

        if os.path.exists(target_path):
            if not os.path.isfile(target_path):
                raise _ExpansionError('Expansion target "{target_path}" exists, but is not a file')
            if not self.overwrite:
                log_message(f'Skip existing file "{expansion_spec.output_path}".')
                return

        if not options.DRY_RUN:
            check_file_exists(source_path)

        create_folder(os.path.dirname(target_path))

        log_message(f'Expand template ({expansion_spec.expansion}).',
                    source=relative_path,
                    target=expansion_spec.output_path)

        try:
            if expansion_spec.expansion == TEMPLATE_EXPANSION:
                _expand_python_template(source_path, target_path, self.symbols)
            elif expansion_spec.expansion == WORD_EXPANSION:
                if self.substitutions is None:
                    self.substitutions = [(re.compile(fr'\b{word}\b'), repl)
                                          for word, repl in self.symbols.items()]
                _expand_regular_expressions(source_path, target_path, self.substitutions)
            else:
                _simple_copy(source_path, target_path, overwrite=self.overwrite)
        except (IOError, OSError, _ExpansionError) as exc:
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except (IOError, OSError) as exc_remove:
                    log_warning('Unable to remove failed target file.',
                                expansion_spec.output_path, exception=exc_remove)
            if isinstance(exc, _ExpansionError):
                raise
            raise _ExpansionError(format_exception(exc))

        _set_permissions(target_path, executable=expansion_spec.executable)

    def _get_expansion_spec(self, relative_path: Text) -> _TemplateExpansionSpec:
        config_expansion_spec = self.expansion_specs_by_path.get(relative_path)
        if config_expansion_spec:
            return config_expansion_spec
        source_folder_path, source_file_name = os.path.split(relative_path)
        target_file_name, extension = os.path.splitext(source_file_name)
        expansion = DEFAULT_EXPANSION
        executable = False
        if extension not in TEMPLATE_EXTENSIONS_ALL:
            expansion = COPY_EXPANSION
            target_file_name += extension
        elif extension == TEMPLATE_EXTENSION_DOT:
            target_file_name = '.' + target_file_name
        elif extension == TEMPLATE_EXTENSION_EXE:
            executable = True
        output_path = os.path.join(source_folder_path, target_file_name)
        generated_spec = _TemplateExpansionSpec(output_path, expansion, executable)
        self.expansion_specs_by_path[relative_path] = generated_spec
        return generated_spec


def _expand_python_template_text(input_text: Text, symbols: Dict) -> Text:
    try:
        return Template(input_text).substitute(symbols)
    except KeyError as exc_key_error:
        raise _ExpansionError(format_message_block('Missing template symbol.',
                                                   symbol=exc_key_error))


# === Public interface.


# Expansion method name constants.
TEMPLATE_EXPANSION = 'template'
WORD_EXPANSION = 'word'
COPY_EXPANSION = 'copy'
ALL_EXPANSIONS = (TEMPLATE_EXPANSION, WORD_EXPANSION, COPY_EXPANSION)
DEFAULT_EXPANSION = TEMPLATE_EXPANSION


def expand_folder(source_root: Text,
                  target_root: Text,
                  sub_folder: Text = None,
                  includes: Sequence[Text] = None,
                  excludes: Sequence[Text] = None,
                  overwrite: bool = False,
                  symbols: Dict = None,
                  ):
    """
    Expand source template folder or sub-folder to target folder.

    Reads source template configuration, if found to determine what kind of
    special handling may be needed.

    :param source_root: template source root folder path
    :param target_root: base target folder
    :param sub_folder: optional relative sub-folder path applied to source and target roots
    :param includes: optional relative paths, supporting wildcards, for files to include
    :param excludes: optional relative paths, supporting wildcards, for files to exclude
    :param overwrite: force overwriting of existing files if True
    :param symbols: symbols used for template expansion
    """
    expander = _TemplateExpander(source_root, overwrite=overwrite, symbols=symbols)
    expander.expand(target_root, sub_folder=sub_folder, includes=includes, excludes=excludes)
