from pathlib import Path
import os 

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