import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import winreg

# import all our custom modules
from get_programs import get_installed_software
from uninstall_program import uninstall_software
from leftover_scan import scan_leftovers, delete_leftover_paths
from manage_windows_apps import get_uwp_apps, uninstall_uwp_app


# ─────────────────────────────────────────────────────────────────
#  HELPER: Check whether a program name appears in Control Panel
# ─────────────────────────────────────────────────────────────────
def is_in_control_panel(software_name):
    """
    Returns True if software_name is found in the Windows registry
    uninstall keys (i.e. it IS listed in Control Panel > Programs).
    """
    registry_locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    name_lower = software_name.lower()
    for root_key, path in registry_locations:
        try:
            reg = winreg.OpenKey(root_key, path)
            for i in range(winreg.QueryInfoKey(reg)[0]):
                try:
                    subkey_name = winreg.EnumKey(reg, i)
                    subkey = winreg.OpenKey(reg, subkey_name)
                    display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                    if name_lower in display_name.lower():
                        return True
                except Exception:
                    pass
        except Exception:
            pass
    return False


# ─────────────────────────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────────────────────────
def create_ui():
    root = tk.Tk()
    root.title("Smart Software Uninstaller")
    root.geometry("780x640")
    root.resizable(False, False)

    try:
        root.iconbitmap("app_logo.ico")
    except Exception:
        pass
    

    app_list_data = []

    # ── MAIN NOTEBOOK (TABS) ──────────────────────────────────────
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both', padx=10, pady=10)

    tab_desktop = ttk.Frame(notebook)
    tab_windows = ttk.Frame(notebook)
    tab_tools   = ttk.Frame(notebook)

    notebook.add(tab_desktop, text="  Desktop Apps  ")
    notebook.add(tab_windows, text="  Windows Apps  ")
    notebook.add(tab_tools,   text="     Tools      ")

    # ── STATUS BAR at the bottom ──────────────────────────────────
    status_var = tk.StringVar(value="Ready.")
    status_bar = tk.Label(root, textvariable=status_var, bd=1,
                          relief=tk.SUNKEN, anchor=tk.W, fg="gray")
    status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

    def set_status(msg):
        status_var.set(msg)
        root.update_idletasks()

    # ─────────────────────────────────────────────────────────────
    #  SHARED: Scan-results pop-up window
    # ─────────────────────────────────────────────────────────────
    def open_scan_results_window(target_name, result_data):
        scan_window = tk.Toplevel(root)
        scan_window.title("Leftover Traces Found")
        scan_window.geometry("580x420")
        scan_window.grab_set()   # make it modal

        tk.Label(scan_window,
                 text=f"Traces found for:  {target_name}",
                 font=("Arial", 11, "bold")).pack(pady=10)

        # scrollable list
        list_frame = tk.Frame(scan_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        result_list = tk.Listbox(list_frame, width=80, height=13,
                                 selectmode=tk.MULTIPLE,
                                 yscrollcommand=scrollbar.set)
        scrollbar.config(command=result_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if result_data:
            for r in result_data:
                result_list.insert(tk.END, r)

            tk.Label(scan_window,
                     text="Select the items you want to permanently delete:",
                     font=("Arial", 9), fg="gray").pack(pady=(6, 0))

            def execute_delete():
                selected_indices = result_list.curselection()
                if not selected_indices:
                    messagebox.showwarning("Nothing Selected",
                                           "Please select at least one item to delete.",
                                           parent=scan_window)
                    return

                confirm = messagebox.askyesno(
                    "Confirm Deletion",
                    f"Permanently delete {len(selected_indices)} selected item(s)?\n\n"
                    "This cannot be undone.",
                    parent=scan_window)
                if not confirm:
                    return

                paths_to_delete = [result_list.get(i) for i in selected_indices]
                set_status("Deleting leftover files…")
                errors = delete_leftover_paths(paths_to_delete)

                if errors:
                    messagebox.showerror(
                        "Deletion Failed",
                        "Could not delete some files.\n"
                        "Make sure you ran this program as Administrator.\n\n"
                        f"Error: {errors[0]}",
                        parent=scan_window)
                    set_status("Deletion failed. Run as Administrator.")
                else:
                    for i in reversed(selected_indices):
                        result_list.delete(i)
                    set_status(f"Successfully deleted {len(paths_to_delete)} leftover(s).")
                    messagebox.showinfo("Done",
                                        "Selected leftovers have been permanently deleted!",
                                        parent=scan_window)
                    if result_list.size() == 0:
                        scan_window.destroy()

            btn_row = tk.Frame(scan_window)
            btn_row.pack(pady=8)
            tk.Button(btn_row, text="Delete Selected",
                      bg="#ffcccc", width=18,
                      command=execute_delete).pack(side=tk.LEFT, padx=8)
            tk.Button(btn_row, text="Close",
                      width=12,
                      command=scan_window.destroy).pack(side=tk.LEFT, padx=8)
        else:
            result_list.insert(tk.END, "✔  No leftover files found. System is clean.")
            tk.Button(scan_window, text="Close",
                      command=scan_window.destroy).pack(pady=10)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 1 – DESKTOP APPS
    # ═══════════════════════════════════════════════════════════════

    def load_software():
        set_status("Loading installed software list…")
        desktop_list.delete(0, tk.END)
        app_list_data.clear()
        software = get_installed_software()
        for item in sorted(software, key=str.lower):   # alphabetical order
            app_list_data.append(item)
            desktop_list.insert(tk.END, item)
        set_status(f"Loaded {len(software)} installed programs.")

    def uninstall():
        selected = desktop_list.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a program to uninstall.")
            return
        name = desktop_list.get(selected[0])          # BUG FIX: use index [0]
        confirm = messagebox.askyesno("Confirm Uninstall",
                                      f"Are you sure you want to uninstall:\n\n  {name}?")
        if confirm:
            set_status(f"Uninstalling: {name}…")
            uninstall_software(name)
            load_software()
            set_status(f"Uninstall command sent for: {name}")

    def search():
        text = search_entry.get().lower()
        desktop_list.delete(0, tk.END)
        for item in app_list_data:
            if text in item.lower():
                desktop_list.insert(tk.END, item)
        matches = desktop_list.size()
        set_status(f"{matches} result(s) found for '{text}'.")

    def scan_selected():
        selected = desktop_list.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a program to scan.")
            return
        name = desktop_list.get(selected[0])          # BUG FIX: use index [0]
        set_status(f"Scanning leftovers for: {name}…")
        result = scan_leftovers(name)
        set_status(f"Scan complete. {len(result)} leftover(s) found for '{name}'.")
        open_scan_results_window(name, result)

    # ── Desktop tab layout ────────────────────────────────────────
    top_frame = tk.Frame(tab_desktop)
    top_frame.pack(pady=10)

    tk.Label(top_frame, text="Search:").pack(side=tk.LEFT, padx=5)
    search_entry = tk.Entry(top_frame, width=42)
    search_entry.pack(side=tk.LEFT, padx=5)
    search_entry.bind("<Return>", lambda e: search())   # Enter key triggers search
    tk.Button(top_frame, text="Search", command=search, width=10).pack(side=tk.LEFT, padx=5)

    list_frame2 = tk.Frame(tab_desktop)
    list_frame2.pack(fill=tk.BOTH, expand=True, padx=10)
    sb2 = tk.Scrollbar(list_frame2)
    desktop_list = tk.Listbox(list_frame2, width=90, height=14, yscrollcommand=sb2.set)
    sb2.config(command=desktop_list.yview)
    sb2.pack(side=tk.RIGHT, fill=tk.Y)
    desktop_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    btn_frame = tk.Frame(tab_desktop)
    btn_frame.pack(pady=6)
    tk.Button(btn_frame, text="Refresh List",   command=load_software,  width=15).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Uninstall App",  command=uninstall,      width=15).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Scan Leftovers", command=scan_selected,  width=15).grid(row=0, column=2, padx=10)

    # ── FORCED UNINSTALL SECTION ─────────────────────────────────
    sep = ttk.Separator(tab_desktop, orient='horizontal')
    sep.pack(fill='x', padx=10, pady=6)

    force_label_frame = tk.LabelFrame(tab_desktop,
                                      text="  Force Clean  (for crack / portable software not in Control Panel)  ",
                                      font=("Arial", 9, "bold"), fg="darkred", padx=10, pady=8)
    force_label_frame.pack(fill='x', padx=12, pady=4)

    force_row = tk.Frame(force_label_frame)
    force_row.pack()

    tk.Label(force_row, text="Software Name:").grid(row=0, column=0, padx=5)
    force_entry = tk.Entry(force_row, width=28)
    force_entry.grid(row=0, column=1, padx=5)
    force_entry.bind("<Return>", lambda e: force_scan())

    # ── KEY FEATURE: Check Control Panel Status ───────────────────
    cp_status_var = tk.StringVar(value="")
    cp_status_label = tk.Label(force_label_frame, textvariable=cp_status_var,
                               font=("Arial", 9, "bold"))
    cp_status_label.pack(pady=(4, 0))

    def check_cp_status():
        """
        Checks if the typed software name is registered in the Windows registry.
        Shows a clear NOT FOUND / FOUND message — the key demo step.
        """
        target_name = force_entry.get().strip()
        if not target_name:
            messagebox.showwarning("Empty", "Please type a software name first.")
            return

        set_status(f"Checking Control Panel registry for: {target_name}…")
        found = is_in_control_panel(target_name)

        if found:
            cp_status_var.set(f'✔  "{target_name}" IS listed in Control Panel. '
                               f'Use the normal Uninstall App button above.')
            cp_status_label.config(fg="green")
            set_status(f'"{target_name}" found in Control Panel registry.')
        else:
            cp_status_var.set(f'✘  "{target_name}" is NOT in Control Panel — '
                               f'use Force Clean below to remove it.')
            cp_status_label.config(fg="red")
            set_status(f'"{target_name}" NOT found in Control Panel. Force Clean required.')

    def force_scan():
        target_name = force_entry.get().strip()
        if not target_name:
            messagebox.showwarning("Empty", "Please type a software name to clean.")
            return
        set_status(f"Force-scanning for leftovers: {target_name}…")
        result = scan_leftovers(target_name)
        set_status(f"Force scan done. {len(result)} leftover(s) found for '{target_name}'.")
        open_scan_results_window(target_name, result)

    def open_control_panel():
        set_status("Opening Windows Control Panel…")
        os.system("control appwiz.cpl")

    btn_row2 = tk.Frame(force_label_frame)
    btn_row2.pack(pady=6)

    tk.Button(btn_row2, text="Check Control Panel",
              bg="#e6e6fa", width=20,
              command=check_cp_status).grid(row=0, column=0, padx=8)

    tk.Button(btn_row2, text="Force Clean",
              bg="#ffcccc", width=15,
              command=force_scan).grid(row=0, column=1, padx=8)

    tk.Button(btn_row2, text="Open Control Panel",
              bg="#e0ffe0", width=18,
              command=open_control_panel).grid(row=0, column=2, padx=8)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 2 – WINDOWS APPS (UWP)
    # ═══════════════════════════════════════════════════════════════

    def load_windows_apps():
        set_status("Loading Windows Store apps…")
        windows_list.delete(0, tk.END)
        uwp_apps = get_uwp_apps()
        for app in sorted(uwp_apps, key=str.lower):
            windows_list.insert(tk.END, app)
        set_status(f"Loaded {len(uwp_apps)} Windows apps.")

    def remove_windows_app():
        selected = windows_list.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an app to uninstall.")
            return
        name = windows_list.get(selected[0])          # BUG FIX: use index [0]
        confirm = messagebox.askyesno("Confirm Uninstall",
                                      f"Uninstall Windows app:\n\n  {name}?")
        if confirm:
            set_status(f"Removing Windows app: {name}…")
            uninstall_uwp_app(name)
            load_windows_apps()

    tk.Label(tab_windows, text="Windows Store Apps (UWP)",
             font=("Arial", 12, "bold")).pack(pady=10)

    win_list_frame = tk.Frame(tab_windows)
    win_list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
    win_sb = tk.Scrollbar(win_list_frame)
    windows_list = tk.Listbox(win_list_frame, width=90, height=20,
                               yscrollcommand=win_sb.set)
    win_sb.config(command=windows_list.yview)
    win_sb.pack(side=tk.RIGHT, fill=tk.Y)
    windows_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    win_btn_frame = tk.Frame(tab_windows)
    win_btn_frame.pack(pady=8)
    tk.Button(win_btn_frame, text="Load Windows Apps",
              width=20, command=load_windows_apps).grid(row=0, column=0, padx=10)
    tk.Button(win_btn_frame, text="Uninstall App",
              width=20, bg="#ffcccc",
              command=remove_windows_app).grid(row=0, column=1, padx=10)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 3 – TOOLS
    # ═══════════════════════════════════════════════════════════════

    tk.Label(tab_tools, text="System Optimization Tools",
             font=("Arial", 12, "bold")).pack(pady=20)

    def launch_tool(cmd):
        set_status(f"Launching: {cmd}")
        os.system(cmd)

    tools_container = tk.Frame(tab_tools)
    tools_container.pack(pady=10)

    tools = [
        ("Task Manager",      "taskmgr"),
        ("Services",          "services.msc"),
        ("System Information","msinfo32"),
        ("Registry Editor",   "regedit"),
        ("Disk Cleanup",      "cleanmgr"),
        ("Programs & Features (Control Panel)", "control appwiz.cpl"),
    ]
    for label, cmd in tools:
        tk.Button(tools_container, text=label, width=38, pady=5,
                  command=lambda c=cmd: launch_tool(c)).pack(pady=4)

    root.mainloop()
