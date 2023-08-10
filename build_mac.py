import os
import re
from build_settings import (
    DIST_DIR,
    WORK_DIR
)
from alphageist import __version__

PYINSTALLER_SPEC_FILE = "main_mac.spec"

def update_spec_file(filename, new_version):
    # Read the content of the file
    with open(filename, 'r') as file:
        content = file.read()

    # Find and replace the current version using regex
    version_pattern = r'(\'CFBundleShortVersionString\':\s*\')(\d+\.\d+\.\d+)(\')'
    
    def replacement(match):
        return match.group(1) + new_version + match.group(3)

    updated_content = re.sub(version_pattern, replacement, content)

    # Write the updated content back to the file
    with open(filename, 'w') as file:
        file.write(updated_content)

    print(f"Version in {PYINSTALLER_SPEC_FILE} updated to {new_version}")

def main():
    update_spec_file(PYINSTALLER_SPEC_FILE, __version__)
    cmd = f"pyinstaller {PYINSTALLER_SPEC_FILE} --clean --noconfirm --distpath {DIST_DIR} --workpath {WORK_DIR}"
    print(cmd)
    failed = os.system(cmd)
    if failed:
        print("Failed to run pyinstaller")
        sys.exit(1)
    
if __name__ == "__main__":
    main()