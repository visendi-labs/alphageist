import logging
import typing
from pathlib import Path
import os 
import codecs
from alphageist import state as s
from alphageist import constant


logger = logging.getLogger(constant.LOGGER_NAME)

def string_to_raw_string(s: str)->str:
    return codecs.unicode_escape_encode(s)[0].decode()


def path_is_valid_format(path):
    try:
        Path(path)
    except Exception:
        return False
    else:
        return True

def is_temp_file(file_path:str) -> bool:
    """Check if a file might be a temporary file by its prefix."""
    temp_prefixes = ['~', '.~']

    # Extract extension and base filename
    filename = os.path.basename(file_path)

    return any(filename.startswith(prefix) for prefix in temp_prefixes)
STATE_SUBSCRIPTION_SIGNATURE = typing.Callable[[s.State, s.State], None]
class StateSubscriptionMixin:
    _state: s.State

    def __init__(self):
        self._state_subscribers = set()

    def subscribe_to_statechange(self, f: STATE_SUBSCRIPTION_SIGNATURE) -> None:
        self._state_subscribers.add(f)

    def unsubscribe_to_statechange(self, f: STATE_SUBSCRIPTION_SIGNATURE) -> None:
        if not f in self._state_subscribers:
            raise ValueError(f"{f} is not a subscriber")
        self._state_subscribers.remove(f)

    def handle_subscription_exception(self):
        raise NotImplementedError

    @property
    def state(self)->s.State:
        return self._state
    
    @state.setter
    def state(self, new_state: s.State)->None:
        old_state = self._state
        if old_state is new_state:
            return
        logger.info(f"{self.__class__.__name__}[{self.state} -> {new_state}]")
        self._state = new_state
        for sub in self._state_subscribers:
            try:
                sub(old_state, new_state)
            except Exception as e:
                self.handle_subscription_exception()
