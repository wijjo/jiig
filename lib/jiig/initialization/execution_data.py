"""
Script execution data.
"""

from dataclasses import dataclass
from typing import Text, List


@dataclass
class ExecutionData:
    """Command line execution data."""
    run_script_path: Text
    tool_script_path: Text
    jiig_root: Text
    jiig_library_path: Text
    cli_args: List[Text]
    parser_implementation: Text
