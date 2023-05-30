from pathlib import Path

def path_is_valid_format(path):
    try:
        Path(path)
    except Exception:
        return False
    else:
        return True
