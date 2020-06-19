"""
Multi-format configuration file load/save support.

This module is used by both the build and the runtime code, since both need to
read configuration files.

It also supports variable substitution using the Python built-in format,
${<name}.
"""

import json
import yaml
from io import StringIO
from string import Template
from typing import Text, Dict


class ConfigurationError(Exception):
    pass


class ConfigBase:
    """Abstract base configuration load/save."""
    def __init__(self, path: Text):
        self.path = path

    def load(self, symbols: Dict = None) -> Dict:
        raise NotImplementedError

    def save(self, data: Dict):
        raise NotImplementedError


class JSONConfig(ConfigBase):
    """JSON configuration load/save."""

    def load(self, symbols: Dict = None) -> Dict:
        try:
            with open(self.path, encoding='utf-8') as json_stream:
                if symbols:
                    json_stream = StringIO(Template(json_stream.read()).substitute(symbols))
                return json.load(json_stream)
        except (IOError, OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError('JSON file read error: {}'.format(exc))

    def save(self, data: Dict):
        try:
            with open(self.path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4)
        except (IOError, OSError) as exc:
            raise ConfigurationError('JSON file write error: {}'.format(exc))


class YAMLConfig(ConfigBase):
    """YAML configuration load/save."""

    def load(self, symbols: Dict = None) -> Dict:
        try:
            with open(self.path, encoding='utf-8') as yaml_stream:
                if symbols:
                    yaml_stream = StringIO(Template(yaml_stream.read()).substitute(symbols))
                return yaml.safe_load(yaml_stream)
        except (IOError, OSError, yaml.YAMLError) as exc:
            raise ConfigurationError('YAML file read error: {}'.format(exc))

    def save(self, data: Dict):
        try:
            with open(self.path, 'w', encoding='utf-8') as yaml_file:
                yaml.dump(data, yaml_file, indent=4)
        except (IOError, OSError, yaml.YAMLError) as exc:
            raise ConfigurationError('YAML file write error: {}'.format(exc))


def for_file(path: Text) -> ConfigBase:
    import os
    extension = os.path.splitext(path)[1]
    if extension == '.json':
        return JSONConfig(path)
    if extension in ['.yaml', '.yaml']:
        return YAMLConfig(path)
    raise ConfigurationError('Unsupported configuration extension: {}'
                             .format(extension))
