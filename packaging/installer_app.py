"""Standalone FRYDAY installer with a branded folder-selection screen."""
from __future__ import annotations

import os
import sys
import threading
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import psutil


APP_VERSION = "0.1.0"
PAYLOAD_NAME = "FRYDAY-Payload.zip"
APP_NAME = "FRYDAY"


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


class FrydayInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("FRYDAY // SETUP")
        self.geometry("820x530")
        self.minsize(780, 500)
        self.configure(fg_color="#070c16")
        try:
            self.iconbitmap(str(resource_path("fryday.ico")))
        except Exception:
            pass

        self._installing = False
        self._installed_path: Path | None = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_layout()

    def _build_layout(self):
        rail = ctk.CTkFrame(self, width=245, corner_radius=0, fg_color="#0b1424")
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_propagate(False)

        reactor = ctk.CTkCanvas(rail, width=116, height=116, bg="#0b1424", highlightthickness=0)
        reactor.pack(pady=(54, 22))
        reactor.create_oval(14, 14, 102, 102, outline="#087fa8", width=2)
        reactor.create_oval(26, 26, 90, 90, outline="#00d9ff", width=2)
        reactor.create_oval(40, 40, 76, 76, outline="#76efff", width=2)
        reactor.create_oval(52, 52, 64, 64, fill="#ccfbff", outline="")
        ctk.CTkLabel(
            rail, text="FRYDAY", font=ctk.CTkFont("Segoe UI", 28, "bold"),
            text_color="#eafaff",
        ).pack()
        ctk.CTkLabel(
            rail, text="PERSONAL DESKTOP ASSISTANT",
            font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#68cde8",
        ).pack(pady=(5, 0))
        ctk.CTkFrame(rail, height=1, fg_color="#193149").pack(fill="x", padx=28, pady=28)
        ctk.CTkLabel(
            rail, text="A smarter desktop\nstarts here.", justify="left",
            font=ctk.CTkFont("Segoe UI", 17, "bold"), text_color="#d6e9f5",
        ).pack(anchor="w", padx=30)
        ctk.CTkLabel(
            rail, text="Version 0.1.0  ·  Windows",
            font=ctk.CTkFont("Segoe UI", 11), text_color="#7590a9",
        ).pack(side="bottom", anchor="w", padx=30, pady=26)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=42, pady=38)
        self.content.grid_columnconfigure(0, weight=1)

        self.heading = ctk.CTkLabel(
            self.content, text="Choose your install location",
            font=ctk.CTkFont("Segoe UI", 25, "bold"), text_color="#f4f9ff",
        )
        self.heading.grid(row=0, column=0, sticky="w")
        self.subtitle = ctk.CTkLabel(
            self.content,
            text="Pick a folder for FRYDAY's application files. You will choose a folder each time setup runs.",
            justify="left", wraplength=480,
            font=ctk.CTkFont("Segoe UI", 12), text_color="#91a9c0",
        )
        self.subtitle.grid(row=1, column=0, sticky="w", pady=(8, 28))

        ctk.CTkLabel(
            self.content, text="INSTALL FOLDER", anchor="w",
            font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#54c8e8",
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))

        path_row = ctk.CTkFrame(self.content, fg_color="transparent")
        path_row.grid(row=3, column=0, sticky="ew")
        path_row.grid_columnconfigure(0, weight=1)
        self.path_entry = ctk.CTkEntry(
            path_row, height=44, placeholder_text="Choose a folder…",
            fg_color="#0c1523", border_color="#25415b", text_color="#e6f4ff",
            placeholder_text_color="#6e8296",
        )
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.path_entry.bind("<KeyRelease>", self._validate_path)
        self.browse_button = ctk.CTkButton(
            path_row, text="Browse", width=96, height=44,
            fg_color="#142a3f", hover_color="#1b3a55", text_color="#d9f7ff",
            border_width=1, border_color="#285675", command=self._browse,
        )
        self.browse_button.grid(row=0, column=1)

        self.path_note = ctk.CTkLabel(
            self.content,
            text="FRYDAY.exe will be placed directly in this folder. Your API key and personal data stay in your Windows profile.",
            justify="left", wraplength=480,
            font=ctk.CTkFont("Segoe UI", 11), text_color="#718aa2",
        )
        self.path_note.grid(row=4, column=0, sticky="w", pady=(10, 16))

        self.desktop_var = ctk.BooleanVar(value=True)
        self.desktop_checkbox = ctk.CTkCheckBox(
            self.content, text="Create a desktop shortcut", variable=self.desktop_var,
            font=ctk.CTkFont("Segoe UI", 12), text_color="#c1d5e8",
            fg_color="#00a8d4", hover_color="#008bb2", border_color="#42617b",
        )
        self.desktop_checkbox.grid(row=5, column=0, sticky="w", pady=(0, 22))

        self.progress_label = ctk.CTkLabel(
            self.content, text="Ready when you are.", anchor="w",
            font=ctk.CTkFont("Segoe UI", 11), text_color="#7f9bb4",
        )
        self.progress_label.grid(row=6, column=0, sticky="ew", pady=(0, 8))
        self.progress = ctk.CTkProgressBar(
            self.content, height=7, corner_radius=4,
            fg_color="#17283a", progress_color="#00c8f0",
        )
        self.progress.set(0)
        self.progress.grid(row=7, column=0, sticky="ew", pady=(0, 24))

        actions = ctk.CTkFrame(self.content, fg_color="transparent")
        actions.grid(row=8, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        self.cancel_button = ctk.CTkButton(
            actions, text="Cancel", width=100, height=42,
            fg_color="transparent", hover_color="#172436", text_color="#9ab0c6",
            command=self.destroy,
        )
        self.cancel_button.grid(row=0, column=1, padx=(0, 10))
        self.install_button = ctk.CTkButton(
            actions, text="Install FRYDAY", width=165, height=42,
            fg_color="#00b8df", hover_color="#0097bd", text_color="#04111b",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            command=self._install,
        )
        self.install_button.configure(state="disabled")
        self.install_button.grid(row=0, column=2)

    def _browse(self):
        chosen = filedialog.askdirectory(
            parent=self,
            title="Choose the folder for FRYDAY",
            mustexist=False,
        )
        if chosen:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, chosen)
            self._validate_path()

    def _selected_path(self) -> Path | None:
        raw = os.path.expandvars(self.path_entry.get().strip())
        if not raw:
            return None
        candidate = Path(raw).expanduser()
        return candidate if candidate.is_absolute() else None

    def _validate_path(self, _event=None):
        path = self._selected_path()
        valid = path is not None and not self._installing
        self.install_button.configure(state="normal" if valid else "disabled")

    @staticmethod
    def _app_is_running() -> bool:
        for process in psutil.process_iter(["name"]):
            try:
                if (process.info.get("name") or "").lower() == "fryday.exe":
                    return True
            except (psutil.Error, OSError):
                continue
        return False

    def _install(self):
        target = self._selected_path()
        if target is None:
            messagebox.showinfo("Choose a folder", "Browse to a folder before installing FRYDAY.", parent=self)
            return
        if self._app_is_running():
            messagebox.showwarning("FRYDAY is open", "Close FRYDAY before installing or updating it.", parent=self)
            return

        if target.exists() and any(target.iterdir()):
            if not messagebox.askyesno(
                "Folder is not empty",
                "This folder already contains files. Continue and let setup replace files with matching names?",
                parent=self,
            ):
                return

        self._installing = True
        self.install_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.desktop_checkbox.configure(state="disabled")
        self.progress_label.configure(text="Installing FRYDAY…")
        desktop_shortcut = self.desktop_var.get()
        threading.Thread(
            target=self._copy_payload,
            args=(target, desktop_shortcut),
            daemon=True,
        ).start()

    def _copy_payload(self, target: Path, desktop_shortcut: bool):
        try:
            payload = resource_path(PAYLOAD_NAME)
            if not payload.is_file():
                raise FileNotFoundError("The embedded FRYDAY setup payload is missing.")

            target.mkdir(parents=True, exist_ok=True)
            root = target.resolve()
            with zipfile.ZipFile(payload) as archive:
                entries = [item for item in archive.infolist() if not item.is_dir()]
                total = max(sum(item.file_size for item in entries), 1)
                copied = 0
                for item in entries:
                    destination = (root / item.filename).resolve()
                    if not destination.is_relative_to(root):
                        raise ValueError("Setup payload contains an invalid path.")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, destination.open("wb") as output:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            output.write(chunk)
                            copied += len(chunk)
                            self.after(0, self.progress.set, min(copied / total, 1.0))

            exe_path = root / "FRYDAY.exe"
            if not exe_path.is_file():
                raise FileNotFoundError("FRYDAY.exe was not found after installation.")
            self._register_install(root)
            self._create_shortcuts(root, desktop_shortcut)
            self._installed_path = root
            self.after(0, self._show_success)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    @staticmethod
    def _register_install(root: Path):
        import winreg

        key_name = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FRYDAY"
        uninstall = root / "uninstall.ps1"
        command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{uninstall}"'
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_name, 0, winreg.KEY_SET_VALUE) as key:
            values = {
                "DisplayName": APP_NAME,
                "DisplayVersion": APP_VERSION,
                "InstallLocation": str(root),
                "UninstallString": command,
            }
            for name, value in values.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    @staticmethod
    def _create_shortcuts(root: Path, desktop: bool):
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            exe = root / "FRYDAY.exe"
            start_menu = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/FRYDAY"
            start_menu.mkdir(parents=True, exist_ok=True)
            shortcut_paths = [start_menu / "FRYDAY.lnk"]
            if desktop:
                import ctypes

                desktop_path = ctypes.create_unicode_buffer(260)
                # CSIDL_DESKTOPDIRECTORY honors OneDrive and other shell redirections.
                result = ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, desktop_path)
                if result == 0 and desktop_path.value:
                    shortcut_paths.append(Path(desktop_path.value) / "FRYDAY.lnk")
            for shortcut_path in shortcut_paths:
                shortcut_path.parent.mkdir(parents=True, exist_ok=True)
                shortcut = shell.CreateShortcut(str(shortcut_path))
                shortcut.TargetPath = str(exe)
                shortcut.WorkingDirectory = str(root)
                shortcut.IconLocation = f"{exe},0"
                shortcut.Save()
        finally:
            pythoncom.CoUninitialize()

    def _show_success(self):
        self._installing = False
        self.heading.configure(text="FRYDAY is ready.")
        self.subtitle.configure(text="Installation completed. Your API key and personal data remain in your Windows profile.")
        self.path_note.configure(text=f"Installed at: {self._installed_path}")
        self.progress_label.configure(text="Install complete")
        self.progress.set(1)
        self.desktop_checkbox.grid_remove()
        self.browse_button.grid_remove()
        self.path_entry.configure(state="disabled")
        self.cancel_button.configure(text="Close", state="normal")
        self.install_button.configure(text="Launch FRYDAY", state="normal", command=self._launch)

    def _show_error(self, error: str):
        self._installing = False
        self.progress_label.configure(text="Installation could not finish")
        self.path_note.configure(text=error, text_color="#ff7c88")
        self.browse_button.configure(state="normal")
        self.cancel_button.configure(state="normal")
        self.path_entry.configure(state="normal")
        self.desktop_checkbox.configure(state="normal")
        self._validate_path()
        messagebox.showerror("FRYDAY setup", error, parent=self)

    def _launch(self):
        if self._installed_path:
            os.startfile(str(self._installed_path / "FRYDAY.exe"))
        self.destroy()


if __name__ == "__main__":
    FrydayInstaller().mainloop()
