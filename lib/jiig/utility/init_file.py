import os
from typing import Text, Any, Dict, Optional, Union, List, Tuple

from .console import abort
from .filesystem import chdir


class NoDefault:
    """Default value type for when no default value is provided."""
    pass


class ParamPayload:
    def __init__(self, default_value: Any = None):
        self.value: Optional[Any] = default_value


class Param:
    """Generic parameter type."""

    def __init__(self, name: Text, default_value: Any = NoDefault):
        """
        Param base class constructor.

        :param name: parameter name
        :param default_value: default value (used as needed by finalize_payload())
        """
        self.name = name
        self.default_value = default_value

    def error(self, message: Text):
        """
        Fatal parameter loading error.

        :param message: error message
        """
        abort(f'init file: {self.name}: {message}')

    def merge_payload_value(self, payload: ParamPayload, value: Any):
        """
        Default merge action overwrites the value.

        :param payload: payload to merge with value
        :param value: value to merge into payload
        """
        payload.value = value

    def finalize_payload(self, payload: ParamPayload):
        """
        If the payload never received a value merge the default value.

        There should be no need to override this method.

        :param payload: payload to finalize
        """
        if self.default_value is NoDefault and payload.value is None:
            self.error('Value is required.')
        if payload.value is None:
            # Use merge_payload_value() so that any necessary tweaking takes place.
            self.merge_payload_value(payload, self.default_value)


class ParamString(Param):
    """Parameter with a text string."""

    def __init__(self,
                 name: Text,
                 default_value: Any = NoDefault):
        super().__init__(name, default_value=default_value)

    def merge_payload_value(self, payload: ParamPayload, value: Text):
        if isinstance(value, str):
            payload.value = value
        else:
            self.error(f'Value is not a string: {value}')


class ParamBoolean(Param):
    """Parameter with a boolean value."""

    def __init__(self,
                 name: Text,
                 default_value: Any = NoDefault):
        super().__init__(name, default_value=default_value)

    def merge_payload_value(self, payload: ParamPayload, value: bool):
        if isinstance(value, bool):
            payload.value = value
        else:
            self.error(f'Value is not a boolean: {value}')


class ParamFolder(ParamString):

    def __init__(self, name: Text, default_value: Text = None):
        super().__init__(name, default_value=default_value)

    def merge_payload_value(self, payload: ParamPayload, value: Text):
        super().merge_payload_value(payload, value)
        payload.value = os.path.abspath(payload.value)


class ParamDict(Param):
    """Parameter with generic dictionary."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[Dict, NoDefault]] = NoDefault):
        super().__init__(name, default_value=default_value or {})

    def dict_of(self, value: Dict) -> Dict:
        if isinstance(value, dict):
            return value
        self.error('Value is not a dictionary.')

    def merge_payload_value(self, payload: ParamPayload, value: Dict):
        if payload.value is None:
            payload.value = {}
        payload.value.update(self.dict_of(value))


class ParamList(Param):
    """Parameter with generic list."""

    def __init__(self,
                 name: Text,
                 unique: bool = False,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        if unique:
            self.unique_values = set()
        else:
            self.unique_values = None
        if default_value is None:
            default_value = []
        super().__init__(name, default_value=default_value)

    def list_of(self, value: Union[List, Text]) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [value]
        self.error(f'Value not a list.')

    def merge_payload_value(self, payload: ParamPayload, value: Union[List, Text]):
        if payload.value is None:
            payload.value = []
        list_value = self.list_of(value)
        if list_value:
            if self.unique_values is not None:
                # Only add unique values and keep track of them for other merges.
                payload.value.extend((
                    item for item in list_value
                    if item not in self.unique_values))
                self.unique_values.update(list_value)
            else:
                payload.value.extend(list_value)


class ParamFolderList(ParamList):
    """Parameter with list of absolute folder paths."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[List, Tuple, Text, NoDefault]] = NoDefault):
        super().__init__(name, default_value=default_value)

    def merge_payload_value(self, payload: ParamPayload, value: Union[List, Text]):
        super().merge_payload_value(
            payload,
            [os.path.abspath(path) for path in self.list_of(value)])


class ParamFolderDict(ParamDict):
    """Parameter with dictionary mapping names to absolute folder paths."""

    def __init__(self,
                 name: Text,
                 default_value: Optional[Union[Dict[Text, Text], NoDefault]] = NoDefault):
        super().__init__(name, default_value=default_value)

    def merge_payload_value(self, payload: ParamPayload, value: Dict[Text, Text]):
        super().merge_payload_value(
            payload,
            {name: os.path.abspath(path) for name, path in self.dict_of(value).items()})


class ParamData(dict):
    """Parameter data dictionary with attribute read access."""
    def __getattr__(self, name: Text) -> Any:
        return self.get(name)


class ParamLoader:
    """Accumulates parameter data from one or more init files."""

    def __init__(self, param_types: List[Param]):
        self._params: Dict[Text, Param] = {}
        self._payloads: Dict[Text, ParamPayload] = {}
        for param_type in param_types:
            self._params[param_type.name] = param_type
            self._payloads[param_type.name] = ParamPayload()

    def get_data(self) -> ParamData:
        """
        Provide parameter data wrapped in a ParamData object.

        :return: ParamData object
        """
        return ParamData({name: payload.value for name, payload in self._payloads.items()})

    def load_file(self, path: Text):
        """
        Load parameter data from an init file in a specified folder.

        :param path: path of init file to load
        """
        # Be forgiving about missing files. Do nothing.
        if os.path.isfile(path):
            # Change the work folder to properly handle relative paths.
            with chdir(os.path.dirname(path), quiet=True):
                symbols = {}
                try:
                    with open(os.path.basename(path), encoding='utf-8') as init_file:
                        init_text = init_file.read()
                except (IOError, OSError) as exc:
                    abort('Unable to read configuration file.',
                          file=os.path.basename(path),
                          exception=exc)
                exec(init_text, symbols)
                for name, value in symbols.items():
                    if name and name[0].isupper():
                        if name not in self._params:
                            self._params[name] = Param(name)
                            self._payloads[name] = ParamPayload()
                        if value is not None:
                            self._params[name].merge_payload_value(self._payloads[name], value)
        for name, payload in self._payloads.items():
            self._params[name].finalize_payload(payload)
