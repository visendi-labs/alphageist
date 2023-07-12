import re
import sys
import os
import threading
import functools
from typing import Iterator
from alphageist import errors
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG

def stream_texts_incrementally(sentences:list[str], repeat_full: int = 40) -> Iterator[str]:
    """Generates an iterator that incrementally increases the sentences. 

    repeat_full defines how many times it should repeat the full sentence before moving on

    For example:
    input: ['hello how are you?', 'Today is Wednesday']
    output: 
    'h' -> 'he' -> 'hel' ... -> 'hello how are you?' -> 'T' ... -> 'Today is Wednesday"
    
    """
    for sentence in sentences:
        for i in range(1, len(sentence) + 1):
            yield sentence[:i]
        for _ in range(repeat_full):
            yield sentence

def change_stylesheet_property(pyqt_obj, css_property, new_value):
    # Get the current stylesheet
    current_style_sheet = pyqt_obj.styleSheet()

    # Create a pattern to find the current border-color
    pattern = re.compile(fr'{css_property}:[\s]*[^;]*;')
    new_style_sheet = re.sub(pattern, f'{css_property}: {new_value};', current_style_sheet)

    # Apply the new stylesheet to the QLineEdit
    pyqt_obj.setStyleSheet(new_style_sheet)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):  # bundled application
        base_path = sys._MEIPASS
    else:  # running in a normal Python environment
        base_path = os.path.abspath(sys.path[0])
        relative_path = os.path.join(relative_path)

    return os.path.join(base_path, relative_path)

def force_main_thread(*argtypes:type):
    """A decorator function that forces a method to be called from the main thread"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if threading.current_thread() != threading.main_thread():
                QMetaObject.invokeMethod(self, func.__name__, Qt.ConnectionType.QueuedConnection,
                                         *(Q_ARG(argtype, arg) for argtype, arg in zip(argtypes, args)),
                                         *(Q_ARG(argtypes[i], kwarg) for i, kwarg in enumerate(kwargs.values())))
            else:
                func(self, *args, **kwargs)
        return wrapper
    return decorator