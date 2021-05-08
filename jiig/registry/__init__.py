"""Registry package symbols."""

from .field import Field, ArgumentAdapter
from .hints import add_supported_hints, add_used_hints, get_bad_hints
from .task_specification import TaskSpecification, TaskReference
from .task_registry import TaskRegistry, register_task
from .tool import Tool, ToolOptions, \
    DEFAULT_AUTHOR, DEFAULT_BUILD_FOLDER, DEFAULT_COPYRIGHT, \
    DEFAULT_DESCRIPTION, DEFAULT_DOC_FOLDER, DEFAULT_TEST_FOLDER, \
    JIIG_VENV_ROOT, SUB_TASK_LABEL, TOP_TASK_LABEL, TOP_TASK_DEST_NAME
