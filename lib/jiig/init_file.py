import os
from typing import Text, Any, Dict, Optional, Union, List, Tuple, Set

from . import constants, utility


class NoDefault:
    """Default value type for when no default value is provided."""
    pass


class ParamPayload:
    def __init__(self, default_value: Any = None):
        self.value: Optional[Any] = default_value


class Param:
    """Generic parameter type."""

    def __init__(self, name: Text, default_value: Any = NoDefault):
        self.name = name
        self.default_value = default_value

    def error(self, message: Text):
        utility.abort(f'{constants.INIT_FILE}: {self.name}: {message}')

    def update(self, payload: ParamPayload, value: Any):
        payload.value = value

    def finalize(self, payload: ParamPayload):
        if self.default_value is NoDefault and payload.value is None:
            self.error('Value is required.')
        if payload.value is None:
            payload.value = self.default_value


class ParamString(Param):
    """Parameter with a text string."""

    def __init__(self,
                 name: Text,
                 default_value: Any = NoDefault,
                 reject_empty: bool = False):
        self.reject_empty = reject_empty
        super().__init__(name, default_value=default_value)

    def update(self, payload: ParamPayload, value: Text):
        if isinstance(value, str):
            payload.value = value
        else:
            self.error(f'Value is not a string: {value}')

    def finalize(self, payload: ParamPayload):
        super().finalize(payload)
        if self.reject_empty and isinstance(payload.value, str) and not payload.value:
            self.error('String value is empty.')


class ParamFolder(ParamString):

    def __init__(self, name: Text):
        super().__init__(name, default_value='')

    def update(self, payload: ParamPayload, value: Text):
        super().update(payload, value)
        payload.value = os.path.abspath(payload.value)


class ParamDict(Param):
    """Parameter with generic dictionary."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[Dict, NoDefault]] = NoDefault):
        super().__init__(name, default_value=default_value or {})

    def update(self, payload: ParamPayload, value: Dict):
        if payload.value is None:
            payload.value = {}
        if isinstance(value, dict):
            payload.value.update(value)
        else:
            self.error('Value is not a dictionary.')


class ParamList(Param):
    """Parameter with generic list."""

    def __init__(self,
                 name: Text,
                 unique: bool = False,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        self.unique = unique
        if default_value is not NoDefault:
            if default_value is None:
                default_value = []
            else:
                default_value = self.list_of(default_value, 'Default value')
        super().__init__(name, default_value=default_value)

    def list_of(self, value: Union[List, Tuple, Text], label: Text) -> List:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [value]
        self.error(f'{label} is not a list.')

    def update(self, payload: ParamPayload, value: Union[List, Text]):
        if payload.value is None:
            payload.value = []
        payload.value.extend(self.list_of(value, 'Value'))

    def finalize(self, payload: ParamPayload):
        super().finalize(payload)
        if self.unique and payload.value:
            # Use dict instead of set, because dict is ordered and set is not.
            payload.value = list(dict.fromkeys(payload.value).keys())


class ParamFolderList(ParamList):
    """Parameter with list of absolute folder paths."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        if default_value is not NoDefault:
            if default_value is None:
                default_value = []
            else:
                default_value = self.path_list(default_value, 'Default value')
        super().__init__(name, default_value=default_value)

    def path_list(self, value: Union[List, Tuple, Text], label: Text) -> List[Text]:
        return [os.path.abspath(path) for path in self.list_of(value or [], label)]

    def update(self, payload: ParamPayload, value: List[Text]):
        super().update(payload, self.path_list(value, 'Value'))


class ParamFolderDict(ParamDict):
    """Parameter with dictionary mapping names to absolute folder paths."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[Dict[Text, Text], NoDefault]] = NoDefault):
        if default_value is not NoDefault and default_value is not None:
            default_value = self.path_dict(default_value)
        super().__init__(name, default_value=default_value)

    @staticmethod
    def path_dict(value: Dict[Text, Text]) -> Dict[Text, Text]:
        return {name: os.path.abspath(path) for name, path in value.items()}

    def update(self, payload: ParamPayload, value: Dict[Text, Text]):
        super().update(payload, self.path_dict(value))


class ParamData(dict):
    """Parameter data dictionary with attribute read access."""
    def __getattr__(self, name: Text) -> Any:
        return self.get(name)


class ParamLoader:
    """Used to accumulate parameter data from init files."""

    def __init__(self, param_types: List[Param]):
        self._params: Dict[Text, Param] = {}
        self._payloads: Dict[Text, ParamPayload] = {}
        for param_type in param_types:
            self._params[param_type.name] = param_type
            self._payloads[param_type.name] = ParamPayload(
                default_value=param_type.default_value)

    def update(self, raw_dict: Dict):
        """Merge parameter data."""
        for name, value in raw_dict.items():
            if name and name[0].isupper():
                if name not in self._params:
                    self._params[name] = Param(name)
                    self._payloads[name] = ParamPayload()
                if value is not None:
                    self._params[name].update(self._payloads[name], value)

    def finalize(self) -> ParamData:
        """Perform final checks and return the parameter data dictionary object."""
        for name in self._params.keys():
            self._params[name].finalize(self._payloads[name])
        return ParamData({name: payload.value for name, payload in self._payloads.items()})

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


def load_files(param_types: List[Param],
               *file_paths: Text) -> ParamData:
    """Load parameter data from multiple files."""
    container = ParamLoader(param_types)
    visited: Set[Text] = set()
    for file_path in file_paths:
        real_path = os.path.realpath(file_path)
        if real_path not in visited:
            visited.add(real_path)
            utility.log_message(f'Load configuration file "{file_path}".',
                                verbose=True)
            container.load_file(file_path)
    return container.finalize()


def load_nearest_file(param_types: List[Param],
                      file_name: Text,
                      folder: Text = None) -> ParamData:
    """Load parameter data from working folder or parent folder."""
    container = ParamLoader(param_types)
    done = False
    while not done:
        path = os.path.join(folder, file_name)
        if os.path.isfile(path):
            container.load_file(path)
            done = True
        else:
            parent_folder = os.path.dirname(folder)
            if parent_folder == folder:
                done = True
            else:
                folder = parent_folder
    return container.finalize()
