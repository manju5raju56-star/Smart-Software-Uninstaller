import os
import subprocess
import shutil

# function to scan leftover files
def scan_leftovers(software_name):
    found = []
    search_paths = [
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        os.path.expanduser("~\\AppData\\Local"),
        os.path.expanduser("~\\AppData\\Roaming")
    ]
    for path in search_paths:
        try:
            for folder in os.listdir(path):
                folder_lower = folder.lower()
                software_lower = software_name.lower()
                if folder_lower == software_lower or folder_lower.startswith(software_lower):
                    found.append(os.path.join(path, folder))
        except OSError:
            pass
    return found

# function to permanently delete the leftover files
def delete_leftover_paths(path_list):
    errors = []
    for path in path_list:
        try:
            # 1. Take Ownership of the folder and everything inside it
            subprocess.run(f'takeown /F "{path}" /R /D Y', shell=True, capture_output=True)
            
            # 2. Grant Full Control permissions to the Administrators group
            subprocess.run(f'icacls "{path}" /grant administrators:F /T', shell=True, capture_output=True)
            
            # 3. Try deleting with Python's native tool
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.isfile(path):
                os.remove(path)
                
            # 4. If it is STILL there, use the CMD fallback
            if os.path.exists(path):
                subprocess.run(f'rmdir /s /q "{path}"', shell=True, capture_output=True)
                
            # 5. Final check
            if os.path.exists(path):
                errors.append("File is actively running in RAM. Reboot required.")
            else:
                print(f"Successfully deleted: {path}")

        except Exception as e:
            errors.append(str(e))
            
    return errors
