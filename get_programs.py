import winreg

# function to get installed software
def get_installed_software():
    all_software = []

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

                    if name not in all_software:
                        all_software.append(name)

                except:
                    pass

        except:
            pass

    return all_software
