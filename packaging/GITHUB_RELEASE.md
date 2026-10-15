# Publish FRYDAY on GitHub

## Before the first push

1. Create a GitHub repository named `fryday-assistant` (public if anyone should download it, private if it is only for you).
2. Keep `.env`, `data/*.json`, `venv`, `build`, `dist`, and `release` out of Git. The root `.gitignore` excludes these files. The setup installer belongs in a GitHub Release asset, not in the source commit.
3. Check the repository's pending files before committing. Never force-add `.env` or your `data` files.

## Create the first release

1. Build the Windows installer with:

   ```powershell
   .\packaging\build_windows.ps1
   ```

2. In GitHub, open the repository and select **Releases** → **Draft a new release**.
3. Create tag `v0.1.0`, use release title `FRYDAY 0.1.0`, and attach `release\FRYDAY-Setup-0.1.0.exe`.
4. Add release notes, then publish. For each later version, increment the version in the packaging files and attach the newly built setup under a new tag.

GitHub Releases distributes the setup file; it does not automatically update installed copies. Users install an update by downloading and running the newer setup again. The modern FRYDAY setup asks for an install folder on every run and starts with the location field blank. FRYDAY keeps its API key and user data in the Windows profile, outside the replaceable app files.

## Current limitations

- This PyInstaller-built installer is unsigned. Windows may show an unknown-publisher/SmartScreen warning. Public distribution should use a code-signing certificate before advertising the download broadly.
- The current folder has no Git repository or GitHub remote yet. Publishing requires creating the GitHub repository and connecting this folder to it.
