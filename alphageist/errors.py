from typing import Set
from alphageist.state import State


class ForbiddenImportError(Exception):
    pass

class MissingConfigComponentsError(Exception):
    missing_keys: Set[str]
    def __init__(self, missing_keys: Set[str]):
        super().__init__(f"Missing config keys: {missing_keys}")
        self.missing_keys = missing_keys

class MissingConfigValueError(Exception):
    keys: Set[str]
    def __init__(self, keys: Set[str]):
        super().__init__(f"The following config keys are not assigned a value: {keys}")
        self.keys = keys

class MissingConfigError(Exception):
    pass
class MissingVectorstoreError(Exception):
    pass

class ConfigValueError(Exception):
    key: str
    value: str
    allowed_values: str
    def __init__(self, key:str, value:str, allowed_values: str):
        super().__init__(f"'{value} is not an allowed value for config key {key}. Allowed values are: {allowed_values}")
        self.key = key
        self.value = value
        self.allowed_values = allowed_values

class NoSupportedFilesInDirectoryError(Exception):
    def __init__(self, directory):
        super().__init__(f"No supported files found in {directory}")

class InvalidStateError(Exception):
    state: State
    allowed_states: Set[State]
    def __init__(self, incorrect_state:State, allowed_states:Set[State]):
        super().__init__(f"This feature is not allowed in current state ({incorrect_state}). " + 
                         f"Allowed states are {', '.join(allowed_states)}")
        self.state = incorrect_state
        self.allowed_states = allowed_states

