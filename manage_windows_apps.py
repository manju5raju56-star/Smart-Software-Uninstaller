import subprocess

# function to get Windows (UWP) apps
def get_uwp_apps():
    # PowerShell command to list all app packages for the current user
    cmd = 'powershell "Get-AppxPackage | Select-Object Name"'
    
    try:
        # Run the command and capture the output text
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        # Clean up the raw PowerShell output into a neat python list
        raw_output = result.stdout.split('\n')
        apps = []
        
        # skip the first 3 lines (which are just PowerShell table headers)
        for line in raw_output[3:]: 
            clean_line = line.strip()
            if clean_line and clean_line not in apps:
                apps.append(clean_line)
                
        return apps
    except Exception as e:
        print("Error loading Windows apps:", e)
        return []

# function to uninstall a Windows app
def uninstall_uwp_app(app_name):
    # PowerShell command to remove a specific app package
    cmd = f'powershell "Get-AppxPackage *{app_name}* | Remove-AppxPackage"'
    
    try:
        subprocess.run(cmd, shell=True)
        print(f"Successfully uninstalled {app_name}")
    except Exception as e:
        print("Error uninstalling app:", e)
