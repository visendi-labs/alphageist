from unittest.mock import Mock
import pytest
from alphageist import util
from alphageist import state
from alphageist import errors


def test_string_to_raw_string():
    s = "\ud835"
    rs = r"\ud835"
    assert util.string_to_raw_string(s) == rs

class A(util.StateSubscriptionMixin):
        def __init__(self, initial_state):
            super().__init__()
            self._state = initial_state

        @util.allowed_states({state.STANDBY, state.LOADING})
        def foo(self):
            pass

def test_state_subscription():
    a = A(state.STANDBY)
    callback_mock = Mock()
    a.subscribe_to_statechange(callback_mock)
    a.state = state.ERROR
    callback_mock.assert_called_once_with(state.STANDBY, state.ERROR)

def test_state_subscription_changed_to_same_state():
    a = A(state.STANDBY)
    callback_mock = Mock()
    a.subscribe_to_statechange(callback_mock)
    a.state = state.STANDBY
    callback_mock.assert_not_called()

def test_state_subscription_subscribe_twice():
    a = A(state.STANDBY)
    callback_mock = Mock()
    a.subscribe_to_statechange(callback_mock)
    a.subscribe_to_statechange(callback_mock)
    a.state = state.ERROR
    callback_mock.assert_called_once_with(state.STANDBY, state.ERROR)

def test_state_subscription_unsubscribe_not_subscribing():
    a = A(state.STANDBY)
    callback_mock = Mock()
    with pytest.raises(ValueError):
        a.unsubscribe_to_statechange(callback_mock)
        
def test_state_subscription_unsubscribe():
    a = A(state.STANDBY)
    callback_mock = Mock()
    a.subscribe_to_statechange(callback_mock)
    a.unsubscribe_to_statechange(callback_mock)
    a.state = state.ERROR
    callback_mock.assert_not_called()

def test_allowed_states():
    a = A(state.STANDBY)
    a.foo()

def test_allowed_states_decorator_incorrect_state():
    a = A(state.ERROR)
    with pytest.raises(errors.InvalidStateError) as exec_info:
        a.foo()

    assert exec_info.value.state == state.ERROR 
    assert exec_info.value.allowed_states == {state.STANDBY, state.LOADING}


