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

class InvalidStateError(Exception):
    def __init__(self, incorrect_state:State, allowed_states:Set[State]):
        super().__init__(f"This feature is not allowed in current state ({incorrect_state}). " + 
                         f"Allowed states are {', '.join(allowed_states)}")