import os
from typing import Text, Any, Dict, Optional, Union, List, Tuple, Set

from . import constants, utility


class NoDefault:
    """Default value type for when no default value is provided."""
    pass


class Param:
    """Generic parameter type."""

    def __init__(self,
                 name: Text,
                 initial_value: Any = None,
                 default_value: Any = NoDefault):
        self.name = name
        self.value = initial_value
        self.default_value = default_value

    def error(self, message: Text):
        utility.abort(f'{constants.INIT_FILE}: {self.name}: {message}')

    def set(self, value: Any):
        self.value = value

    def finalize(self):
        if self.default_value is NoDefault and self.value is None:
            self.error('Value is required.')
        if self.value is None:
            self.value = self.default_value


class ParamString(Param):
    """Parameter with a text string."""

    def __init__(self,
                 name: Text,
                 initial_value: Text = None,
                 default_value: Any = NoDefault,
                 reject_empty: bool = False):
        self.reject_empty = reject_empty
        if initial_value is not None and not isinstance(initial_value, str):
            self.error('Initial value is not a string.')
        super().__init__(name,
                         initial_value=initial_value,
                         default_value=default_value)

    def set(self, value: Text):
        if not isinstance(value, str):
            self.error('Value is not a string.')
        super().set(value)

    def finalize(self):
        super().finalize()
        if self.reject_empty and isinstance(self.value, str) and not self.value:
            self.error('String value is empty.')


class ParamFolder(ParamString):

    def __init__(self,
                 name: Text,
                 initial_value: Text = None):
        super().__init__(name, initial_value=initial_value, default_value='')

    def set(self, value: Text):
        super().set(os.path.abspath(value))


class ParamDict(Param):
    """Parameter with generic dictionary."""

    def __init__(self,
                 name: Text,
                 initial_value: Dict = None,
                 default_value: Optional[Union[Dict, NoDefault]] = NoDefault):
        if initial_value is not None and not isinstance(initial_value, dict):
            self.error('Initial value is not a dictionary.')
        if default_value is None:
            default_value = {}
        super().__init__(name,
                         initial_value=initial_value,
                         default_value=default_value)

    def set(self, value: Dict):
        if not isinstance(value, dict):
            self.error('Value is not a dictionary.')
        if self.value is None:
            self.value = {}
        self.value.update(value)


class ParamList(Param):
    """Parameter with generic list."""

    def __init__(self,
                 name: Text,
                 unique: bool = False,
                 initial_value: Union[List, Tuple, Text] = None,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        self.unique = unique
        if initial_value is not None:
            initial_value = self.list_of(initial_value, 'Initial value')
        if default_value is not NoDefault:
            if default_value is None:
                default_value = []
            else:
                default_value = self.list_of(default_value, 'Default value')
        super().__init__(name,
                         initial_value=initial_value,
                         default_value=default_value)

    def list_of(self, value: Union[List, Tuple, Text], label: Text) -> List:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [value]
        self.error(f'{label} is not a list.')

    def set(self, value: Union[List, Text]):
        if self.value is None:
            self.value = []
        self.value.extend(self.list_of(value, 'Value'))

    def finalize(self):
        super().finalize()
        if self.unique and self.value:
            # Use dict instead of set, because dict is ordered and set is not.
            self.value = list(dict.fromkeys(self.value).keys())


class ParamFolderList(ParamList):
    """Parameter with list of absolute folder paths."""

    def __init__(self,
                 name: Text,
                 initial_value: Union[List, Tuple, Text] = None,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        if initial_value is not None:
            initial_value = self.path_list(initial_value, 'Initial value')
        if default_value is not NoDefault:
            if default_value is None:
                default_value = []
            else:
                default_value = self.path_list(default_value, 'Default value')
        super().__init__(name,
                         initial_value=initial_value,
                         default_value=default_value)

    def path_list(self, value: Union[List, Tuple, Text], label: Text) -> List[Text]:
        return [os.path.abspath(path) for path in self.list_of(value or [], label)]

    def set(self, value: List[Text]):
        if self.value is None:
            self.value = []
        super().set(self.path_list(value, 'Value'))


class ParamFolderDict(ParamDict):
    """Parameter with dictionary mapping names to absolute folder paths."""

    def __init__(self,
                 name: Text,
                 initial_value: Dict[Text, Text] = None,
                 default_value: Optional[Union[Dict[Text, Text], NoDefault]] = NoDefault):
        if initial_value is not None:
            initial_value = self.path_dict(initial_value)
        if default_value is not NoDefault and default_value is not None:
            default_value = self.path_dict(default_value)
        super().__init__(name,
                         initial_value=initial_value,
                         default_value=default_value)

    @staticmethod
    def path_dict(value: Dict[Text, Text]) -> Dict[Text, Text]:
        return {name: os.path.abspath(path) for name, path in value.items()}

    def set(self, value: Dict[Text, Text]):
        if self.value is None:
            self.value = {}
        super().set(self.path_dict(value))


class ParamData(dict):
    """Parameter data dictionary with attribute read access."""
    def __getattr__(self, name: Text) -> Any:
        return self.get(name)


class ParamContainer:
    """Used to accumulate parameter data from init files."""

    def __init__(self, param_types: List[Param]):
        self._params = {param.name: param for param in param_types}

    def update(self, raw_dict: Dict):
        """Merge parameter data."""
        for name, value in raw_dict.items():
            if name and name[0].isupper():
                if name not in self._params:
                    self._params[name] = Param(name)
                if value is not None:
                    self._params[name].set(value)

    def finalize(self) -> ParamData:
        """Perform final checks and return the parameter data dictionary object."""
        for param in self._params.values():
            param.finalize()
        return ParamData({name: param.value for name, param in self._params.items()})

    def load_file(self, path: Text):
        """
        Load parameter data from an init file in a specified folder.

        Does NOT finalize the data, so nothing is returned.
        """
        # Be forgiving about missing files. Do nothing.
        if not os.path.isfile(path):
            return
        # Change the work folder to properly handle relative paths.
        original_folder_path = os.getcwd()
        os.chdir(os.path.dirname(path))
        try:
            symbols = {}
            try:
                with open(os.path.basename(path), encoding='utf-8') as init_file:
                    init_text = init_file.read()
            except (IOError, OSError) as exc:
                utility.abort('Unable to read configuration file.',
                              file=os.path.basename(path),
                              exception=exc)
            exec(init_text, symbols)
            self.update(symbols)
        finally:
            os.chdir(original_folder_path)


def load(param_types: List[Param],
         folders: List[Text],
         file_name: Text) -> ParamData:
    """Load parameter data from multiple folders with a common file name."""
    container = ParamContainer(param_types)
    visited: Set[Text] = set()
    for folder in folders:
        full_folder_path = os.path.realpath(folder)
        if full_folder_path not in visited:
            visited.add(full_folder_path)
            file_path = os.path.join(full_folder_path, file_name)
            container.load_file(file_path)
    return container.finalize()
