import re

def change_stylesheet_property(pyqt_obj, css_property, new_value):
    # Get the current stylesheet
    current_style_sheet = pyqt_obj.styleSheet()

    # Create a pattern to find the current border-color
    pattern = re.compile(fr'{css_property}:[\s]*[^;]*;')
    new_style_sheet = re.sub(pattern, f'{css_property}: {new_value};', current_style_sheet)

    # Apply the new stylesheet to the QLineEdit
    pyqt_obj.setStyleSheet(new_style_sheet)