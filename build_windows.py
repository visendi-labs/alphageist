import os
import sys
import shutil
from main import __version__

print(f"version: {__version__}")

TEMPLATE_FILE = "template.ifp"  
NEW_FILE = os.path.join('dist', f'install_settings_{__version__}.ifp')
DIST_FOLDER = os.path.join('dist', 'Visendi Search')
PYINSTALLER_SPEC_FILE = "main_windows.spec"

def update_version_number_in_ifp():
    print(f"changing version number to {__version__}")
    with open(NEW_FILE, 'r') as file:
        lines = file.readlines()

    # change the version number
    for i, line in enumerate(lines):
        if "<<version>>" in line:
            lines[i] = line.replace("<<version>>", __version__)

    # write the changes back to the file
    with open(NEW_FILE, 'w') as file:
        file.writelines(lines)

def remove_files_and_folders_in_ifp():
    print("Removing all files and folders...")
    with open(NEW_FILE, 'r') as file:
        lines = file.readlines()

    start = 0
    for i, line in enumerate(lines):
        if "[Files/Dirs]" in line:
            start = i+1
        if start:
            if "[Licence_Begin]" in line:
                stop = i

    del lines[start:stop]

    # write the changes back to the file
    with open(NEW_FILE, 'w') as file:
        file.writelines(lines)


def insert_new_files_and_folders():
    # now add the new files and folders from dist_folder
    print("Inserting new files and folders....")

    new_lines = []
    n_folders, n_files = 0, 0
    for entry in os.scandir(DIST_FOLDER):
        if os.path.isfile(entry.path):
            file_size = os.path.getsize(entry.path)/1024
            new_lines.append(f'{os.path.abspath(entry.path)}\n{os.path.splitext(entry.name)[1][1:]}\n{file_size} KB\n')
            n_files += 1
        elif os.path.isdir(entry.path):
            new_lines.append(f'{os.path.abspath(entry.path)}\nN/A\n[Folder]\n') 
            n_folders += 1
    print(f"Added {n_folders} folders and {n_files} files")

    with open(NEW_FILE, 'r') as file:
        template_lines = file.readlines()

    start = template_lines.index('[Files/Dirs]\n')
    final_list = template_lines[:start+1] + new_lines + template_lines[start+1:]

    with open(NEW_FILE, 'w') as f:
        for line in final_list:
            f.write(line)  # add a newline character after each line

def main():
    print("Running pyinstaller...")
    failed = os.system(f"pyinstaller {PYINSTALLER_SPEC_FILE} --noconfirm")
    if failed:
        print("Failed to run pyinstaller")
        sys.exit(1)

    print("Building install forge setup file...")
    # Copy the template file
    print(f"Copying {TEMPLATE_FILE} to {NEW_FILE}")
    shutil.copy2(TEMPLATE_FILE, NEW_FILE)

    update_version_number_in_ifp()
    remove_files_and_folders_in_ifp()
    insert_new_files_and_folders()
    print("Done")

if __name__ == "__main__":
    main()




