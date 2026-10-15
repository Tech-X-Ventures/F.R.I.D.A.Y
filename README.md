# FRYDAY

FRYDAY is a Windows desktop AI assistant built in Python. It combines a voice-enabled desktop interface with conversational AI, app launching, basic system controls, and system-status information.

## Install FRYDAY

1. Open [FRYDAY Releases](https://github.com/Tech-X-Ventures/F.R.I.D.A.Y/releases) and download the latest `FRYDAY-Setup-<version>.exe` file.
2. Run the setup file. Windows may show an unknown-publisher warning because the installer is not code-signed.
3. Select **Browse** and choose a dedicated folder for FRYDAY. For example, create a new folder named `FRYDAY` in a location you choose. Setup's location field starts blank on every run, so select the folder explicitly.
4. Choose whether to add a desktop shortcut, then select **Install FRYDAY**. Setup also adds FRYDAY to the Start menu. If the selected folder already contains files, setup asks before replacing files with matching names.
5. Open FRYDAY. If no API key is configured, FRYDAY displays an AI setup window asking you to select Groq or OpenAI and enter your own API key.

The installer does not contain an API key. Any key or placeholder used for a demonstration has been removed and is not a working credential. Each user must provide their own key to use AI chat. The key is saved locally in the current Windows profile at `%APPDATA%\FRYDAY\.env`; it is not uploaded with the installer. Select **Continue without AI** to use supported local commands without AI chat, or add a key later in the app settings.

After saving a key, send FRYDAY a simple question to check the connection. The provider is contacted when the first AI request is made. If the key is rejected or a connection error occurs, note the error and report it through GitHub Issues. **Do not include your API key** in an issue, screenshot, or comment.

The setup keeps the app's program files in the folder you choose. FRYDAY also creates shortcuts and an uninstall entry in Windows. Its settings, API key, and personal data are kept separately in your Windows profile. FRYDAY can perform supported desktop actions when you ask it to; review commands before using them.

### Update FRYDAY

Updates are currently installed manually; FRYDAY does not update itself automatically.

1. Download the newer setup file from [Releases](https://github.com/prateeksharmai8/fryday-assistant/releases).
2. Close FRYDAY before running setup.
3. Run the newer setup and browse to the same folder as the current installation. Setup starts with a blank location field every time.
4. Confirm the prompt to continue when the folder already contains files.

The update replaces app files with matching names. Your API key, settings, profile, and chat data are stored separately under `%APPDATA%\FRYDAY` and are kept during an update.

### Uninstall and remove personal data

Uninstall FRYDAY from **Windows Settings → Apps → Installed apps → FRYDAY → Uninstall**. The uninstaller removes the app files and shortcuts, but keeps `%APPDATA%\FRYDAY` so your settings and data remain available if you reinstall.

To remove FRYDAY's saved API key, settings, profile, and chat history too, first uninstall FRYDAY, then delete the `%APPDATA%\FRYDAY` folder in File Explorer. This also removes any saved FRYDAY profile and conversation history.

## API key setup

Each person who wants AI chat needs their own API key. In FRYDAY's AI setup window, select a provider and follow the displayed link to create a key:

- [Get a Groq API key](https://console.groq.com/keys)
- [Get an OpenAI API key](https://platform.openai.com/api-keys)

Keep your key private. Do not paste it into an issue, commit it to Git, or share it with another person. The installer and public source repository should never contain a personal API key.

## Features

- Dark desktop interface with an animated Arc Reactor-style HUD.
- Voice input and spoken responses.
- Conversational AI through a user-provided Groq or OpenAI API key.
- Local fast-path handling for supported basic commands without an API key.
- App launching, volume controls, and CPU, memory, battery, and storage status.
- Website, YouTube, weather, date, and time requests.
- Optional profile and conversation memory stored in the current Windows user profile.

## Example commands

- “Open Notepad” or “Launch Chrome”
- “Run diagnostics” or “How much RAM do I have left?”
- “Volume up” or “Mute sound”
- “What time is it?” or “What’s the weather in Mumbai?”
- “Open YouTube” or “Play AC/DC Back in Black on YouTube”
- “Remember that I prefer concise answers”

Available commands depend on your Windows setup, microphone, network connection, and whether an API key is configured.

## Run from source

The installed setup is the simplest way to use FRYDAY. To run the Python source for development, use PowerShell from the project folder:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

The source app asks for an API key when needed. Local `.env` files and personal JSON data are excluded from Git by `.gitignore`; never force-add them.

Before making the source repository public, review the starter profile in `core/memory.py`. Runtime profile and chat files are ignored, but default values written directly in source code are visible to everyone who can view the repository.

To build the Windows installer from source:

```powershell
.\packaging\build_windows.ps1
```

The installer is generated at `release\FRYDAY-Setup-0.1.0.exe`. The setup executable is published as a GitHub Release asset, not committed with the source files.

## Project structure

```text
core/        Assistant logic, configuration, voice, memory, and Windows controls
gui/         FRYDAY desktop interface and API-key setup window
packaging/   Windows app and setup build scripts
tests/       Automated and optional live desktop checks
main.py      Application entry point
```

Personal settings, API credentials, and conversation files are created locally at runtime. They are not part of the public source release.
