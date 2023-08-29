import logging
import threading
import typing
from pathlib import Path
import os 
import codecs
import functools
from alphageist import state as s
from alphageist import constant
from alphageist import errors


logger = logging.getLogger(constant.LOGGER_NAME)
class LoadingContext:
    _lock: threading.Lock
    total_files: typing.Optional[int]
    current_file: typing.Optional[str]
    cancel_event: threading.Event
    def __init__(self):
        self._lock = threading.Lock()
        self.total_files = 1
        self.files_loaded = 0
        self.current_file = None
        self.cancel_event = threading.Event()

    @property
    def files_loaded(self) -> int:
        with self._lock:
            return self._files_loaded

    @files_loaded.setter
    def files_loaded(self, value: int):
        with self._lock:
            self._files_loaded = value

    def cancel(self):
        self.cancel_event.set()

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

def set_logging_level(level: str):
    levels = logging._nameToLevel
    logger = logging.getLogger(constant.LOGGER_NAME)
    logger.setLevel(levels[level])
    for handler in logger.handlers:
        handler.setLevel(levels[level])

def string_to_raw_string(s: str)->str:
    return codecs.unicode_escape_encode(s)[0].decode()

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


def allowed_states(required_states:typing.Set[s.State]):
    """
    Decorator for methods that should only be called when an object is in a specific state.

    Args:
        required_states (set): The set of states in which the decorated method is allowed to be called.

    Returns:
        function: The decorated function, which will now include a check to make sure 
                  that the method is only called when the object is in one of the required states.

    Raises:
        InvalidStateError: If the object's current state is not in the set of required states.
    """
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.state not in required_states:
                raise errors.InvalidStateError(self.state, required_states)
            return func(self, *args, **kwargs)
        return wrapper
    return actual_decorator