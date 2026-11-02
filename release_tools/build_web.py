"""Create the local Web edition source distribution."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
output = root / "dist" / "CapCut-Keyframe-Studio-Web.zip"
output.parent.mkdir(exist_ok=True)
files = [root / name for name in (
    "run.py", "server.py", "desktop_app.py", "desktop_update.py", "desktop_widgets.py", "requirements.txt",
    "LICENSE", "RELEASE_GUIDE.md", "start_web.bat", "start_web.sh",
)]
files += list((root / "core").glob("*.py"))
files += [p for p in (root / "web").rglob("*") if p.is_file()]
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(root))
print(output)
