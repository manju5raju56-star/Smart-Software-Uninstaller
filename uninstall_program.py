import winreg
import subprocess

# function to uninstall software
def uninstall_software(software_name):

    registry_locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for root, path in registry_locations:
        try:
            reg = winreg.OpenKey(root, path)

            for i in range(winreg.QueryInfoKey(reg)[0]):
                try:
                    subkey_name = winreg.EnumKey(reg, i)
                    subkey = winreg.OpenKey(reg, subkey_name)

                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")

                    if name == software_name:
                        uninstall_cmd, _ = winreg.QueryValueEx(subkey, "UninstallString")
                        subprocess.call(uninstall_cmd, shell=True)
                        return

                except:
                    pass

        except:
            pass
