"""Build on the target OS: python release_tools/build.py."""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
args = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
    "--windowed", "--name", "CapCut Keyframe Studio",
    "--add-data", f"web{os.pathsep}web",
    "--add-data", f"LICENSE{os.pathsep}.",
    "--hidden-import", "desktop_app",
    "--hidden-import", "server",
    "--collect-all", "PIL",
]
if sys.platform == "darwin":
    args += ["--icon", "AppIcon.icns", "--osx-bundle-identifier", "com.capcut.keyframestudio"]
args += ["run.py"]
subprocess.run(args, check=True)

if sys.platform == "win32":
    iscc = shutil.which("ISCC") or r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    subprocess.run([iscc, "release_tools/windows.iss"], check=True)
elif sys.platform == "darwin":
    staging = ROOT / "build" / "dmg-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copytree(ROOT / "dist" / "CapCut Keyframe Studio.app", staging / "CapCut Keyframe Studio.app")
    os.symlink("/Applications", staging / "Applications")
    shutil.copy2(ROOT / "RELEASE_GUIDE.md", staging / "READ_ME.md")
    output = ROOT / "dist" / f"CapCut-Keyframe-Studio-macOS-{platform.machine()}.dmg"
    if output.exists():
        output.unlink()
    subprocess.run(["hdiutil", "create", "-volname", "CapCut Keyframe Studio",
                    "-srcfolder", str(staging), "-ov", "-format", "UDZO", str(output)], check=True)
else:
    raise SystemExit("Desktop installers must be built on Windows or macOS.")
