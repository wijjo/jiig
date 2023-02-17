# Copyright (C) 2020-2023, Steven Cooper
#
# This file is part of Jiig.
#
# Jiig is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jiig is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jiig.  If not, see <https://www.gnu.org/licenses/>.

"""Runtime object initialization."""

from types import ModuleType
from typing import Type

from jiig.action_context import ActionContext
from jiig.runtime import Runtime
from jiig.tool import ToolMetadata, ToolPaths
from jiig.util.class_resolver import ClassResolver
from jiig.util.log import abort

from .help import HelpGenerator


def prepare_runtime_object(*,
                           runtime_spec: Type[Runtime] | str | ModuleType | None,
                           metadata: ToolMetadata,
                           argument_data: object,
                           paths: ToolPaths,
                           help_generator: HelpGenerator,
                           extra_symbols: dict,
                           ) -> Runtime:
    """
    Prepare runtime object passed to task functions.

    :param runtime_spec: runtime class specification
    :param metadata: runtime metadata
    :param argument_data: argument data
    :param paths: runtime paths
    :param help_generator: help generator
    :param extra_symbols: extra application symbols in Runtime object
    :return: prepared runtime object
    """
    if runtime_spec is None:
        runtime_spec = Runtime
    context_resolver = ClassResolver(ActionContext, 'runtime')
    runtime_registration = context_resolver.resolve_class(runtime_spec)

    runtime_class = runtime_registration.subclass
    assert issubclass(runtime_class, Runtime)
    try:
        runtime_instance = runtime_class(
            None,
            help_generator=help_generator,
            data=argument_data,
            meta=metadata,
            paths=paths,
            **extra_symbols,
        )
        return runtime_instance
    except Exception as exc:
        abort(f'Exception while creating runtime class {runtime_class.__name__}',
              exc,
              exception_traceback_skip=1)
