# CapCut Keyframe Studio 0.2 Preview

## Windows
Run CapCut-Keyframe-Studio-Windows-Setup.exe. The installer adds Desktop and local Web shortcuts to the Start menu. Python is bundled.

Install FFmpeg separately for video previews, audio analysis and stabilization:
```powershell
winget install --id Gyan.FFmpeg --exact
```
Restart the app after installation.

## macOS
Choose the DMG matching your processor (arm64 for Apple Silicon, x86_64 for Intel).
Drag the app to Applications. Python and Pillow are bundled.
Install FFmpeg using Homebrew: `brew install ffmpeg`.
The preview builds are unsigned and not notarized. macOS may require approval in System Settings > Privacy & Security.

To open the local Web edition from an installed app:
```sh
open -a "CapCut Keyframe Studio" --args --web
```

## Web edition
This release contains a local Web server, because CapCut project drafts and source media live on your computer. It is not a public hosted service.

Extract CapCut-Keyframe-Studio-Web.zip, install Python 3.11+ and FFmpeg, then run:
```sh
python3 -m pip install -r requirements.txt
python3 run.py --web
```
On Windows, use `py -3` instead of `python3`.
Open http://localhost:8765. Keep the launcher running while editing.
The start_web scripts can be used after installing the requirements.

Save or close your project in CapCut before editing it. Select your local draft directory in the app.
Keep automatic backups and verify your project in CapCut after applying changes.

## Public hosting
The current filesystem-based API must not be exposed as a public multi-user service.
A hosted edition needs isolated per-user project/media import, access control and draft export.
No public hosted endpoint is included in this release.

## Build and validation
Install `requirements-build.txt` and run `python release_tools/build.py` on Windows/macOS.
Windows builds require Inno Setup 6. macOS builds use hdiutil.
Run `python release_tools/build_web.py` for the local Web archive.
CI checks Python compilation, JavaScript syntax, API startup, media-frame proportions and desktop startup before publishing preview installers.
