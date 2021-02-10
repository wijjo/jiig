"""
Tool runtime data derived from Tool configuration.
"""

from dataclasses import dataclass
from typing import Text, List, Dict, Any

from jiig import config


@dataclass
class ToolRuntime:
    """
    Tool runtime data.

    Copied and derived from Tool specification. Tool attributes that are only
    used during initialization are omitted from Application runtime data.
    """

    # === Meta-data.

    name: Text
    """Tool name."""

    description: Text
    """Tool description."""

    author: Text
    """Tool author name."""

    copyright: Text
    """Tool copyright."""

    version: Text
    """Tool version identifier."""

    project_name: Text
    """Project name for documentation."""

    # === Virtual environment configuration.

    venv_folder: Text
    """Virtual environment root folder."""

    pip_packages: List[Text]
    """Packages needed by virtual environment, if enabled."""

    # === Documentation/help parameters.

    doc_api_packages: List[Text]
    """Package names for producing API documentation."""

    doc_api_packages_excluded: List[Text]
    """Package names to exclude from API documentation."""

    sub_task_label: Text
    """Name used to label sub-task types."""

    top_task_label: Text
    """Name used to label the top level task type."""

    # === Filesystem paths.

    tool_root_folder: Text
    """Tool base (root) folder."""

    jiig_root_folder: Text
    """Jiig base (root) folder."""

    library_folders: List[Text]
    """Library folders to add to Python import path."""

    build_folder: Text
    """Build output folder, if applicable."""

    doc_folder: Text
    """Documentation output folder, e.g. for Pdoc3 documentation."""

    aliases_path: Text
    """Path to aliases file."""

    test_folder: Text
    """Test folder path for loading unit tests."""

    # === Other runtime data.

    options: config.ToolOptions
    """Various boolean tool behavior options."""

    expansion_symbols: Dict[Text, Any]
    """Symbols used for string and path template expansion."""
