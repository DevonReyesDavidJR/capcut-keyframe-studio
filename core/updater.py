"""GitHub release discovery, verified downloads and detached native installers."""
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import ssl
import certifi
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from core.version import APP_VERSION, REPOSITORY

API = "https://api.github.com/repos/" + REPOSITORY
MAX_DOWNLOAD = 512 * 1024 * 1024

def version_key(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:-preview\.(\d+))?", value)
    if not match:
        raise ValueError("Phiên bản GitHub không đúng định dạng")
    major, minor, patch, preview = match.groups()
    return (int(major), int(minor), int(patch), 1 if preview is None else 0, int(preview or 0))

def asset_name(system=None, machine=None):
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if system == "Darwin":
        arch = "arm64" if machine in ("arm64", "aarch64") else "x86_64" if machine in ("x86_64", "amd64") else None
        if arch:
            return f"CapCut-Keyframe-Studio-macOS-{arch}.dmg"
    if system == "Windows" and machine in ("amd64", "x86_64"):
        return "CapCut-Keyframe-Studio-Windows-Setup.exe"
    raise ValueError("Chưa có bộ cài cho hệ điều hành/kiến trúc này")

def trusted_asset(url):
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == "github.com" and parsed.path.startswith("/" + REPOSITORY + "/releases/download/")

def _open(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        "User-Agent": "CapCut-Keyframe-Studio/" + APP_VERSION,
        "Accept": "application/vnd.github+json" if url.startswith(API) else "application/octet-stream",
    }), timeout=30, context=ssl.create_default_context(cafile=certifi.where()))

def _read(url, limit=2 * 1024 * 1024):
    with _open(url) as response:
        result = response.read(limit + 1)
    if len(result) > limit:
        raise ValueError("Phản hồi GitHub vượt giới hạn")
    return result

def find_update(current=APP_VERSION, include_preview=None, releases=None, system=None, machine=None):
    if include_preview is None:
        include_preview = "-preview." in current
    if releases is None:
        releases = json.loads(_read(API + "/releases?per_page=50"))
    candidates = []
    wanted = asset_name(system, machine)
    for release in releases:
        if release.get("draft") or (release.get("prerelease") and not include_preview):
            continue
        try:
            key = version_key(release.get("tag_name", ""))
        except ValueError:
            continue
        if key <= version_key(current):
            continue
        assets = {a["name"]: a for a in release.get("assets", [])}
        asset, checksums = assets.get(wanted), assets.get("SHA256SUMS.txt")
        if not asset or not checksums:
            continue
        if not trusted_asset(asset.get("browser_download_url", "")) or not trusted_asset(checksums.get("browser_download_url", "")):
            continue
        candidates.append((key, release, asset, checksums))
    if not candidates:
        return None
    _, release, asset, checksums = max(candidates, key=lambda c: c[0])
    return {"version": release["tag_name"].lstrip("v"), "notes": release.get("body") or "",
            "url": "https://github.com/" + REPOSITORY + "/releases/tag/" + urllib.parse.quote(release["tag_name"], safe=""),
            "asset": asset, "checksums": checksums}

def checksum_for(text, filename):
    for line in text.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) == 2 and fields[1].lstrip("*") == filename and re.fullmatch("[a-fA-F0-9]{64}", fields[0]):
            return fields[0].lower()
    raise ValueError("Bản phát hành thiếu SHA-256 cho bộ cài này")

def download(update, progress=lambda value: None, cancelled=lambda: False):
    asset = update["asset"]
    if not trusted_asset(asset["browser_download_url"]) or not trusted_asset(update["checksums"]["browser_download_url"]):
        raise ValueError("Đường dẫn bộ cài không thuộc kho GitHub của app")
    name = asset["name"]
    if name != Path(name).name or not name.endswith((".dmg", ".exe")):
        raise ValueError("Tên bộ cài không hợp lệ")
    expected = checksum_for(_read(update["checksums"]["browser_download_url"]).decode("utf-8"), name)
    size = int(asset.get("size", 0))
    if size <= 0 or size > MAX_DOWNLOAD:
        raise ValueError("Kích thước bộ cài không hợp lệ")
    directory = Path(tempfile.mkdtemp(prefix="keyframe-update-"))
    target = directory / name
    partial = directory / (name + ".part")
    try:
        digest, count = hashlib.sha256(), 0
        with _open(asset["browser_download_url"]) as response, partial.open("wb") as stream:
            while True:
                if cancelled():
                    raise RuntimeError("Đã hủy tải cập nhật")
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > size or count > MAX_DOWNLOAD:
                    raise ValueError("Dung lượng tải về không khớp")
                stream.write(chunk)
                digest.update(chunk)
                progress(min(100, count * 100 / size))
        if count != size or digest.hexdigest() != expected:
            raise ValueError("SHA-256 không khớp. Bộ cài đã bị loại bỏ; app hiện tại được giữ nguyên.")
        partial.rename(target)
        return target
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise

MAC_HELPER = r"""#!/bin/sh
pid="$1"; target="$2"; staged="$3"; backup="$4"
fail() {
  /usr/bin/osascript -e 'display alert "Không thể cập nhật Keyframe Studio" message "Bản cũ đã được giữ lại. Hãy mở lại app và thử cập nhật lần nữa."'
  exit 1
}
attempt=0
while /bin/kill -0 "$pid" 2>/dev/null; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 120 ] || fail
  /bin/sleep 1
done
had_old=0
if [ -e "$target" ]; then
  /bin/mv "$target" "$backup" || fail
  had_old=1
fi
if ! /bin/mv "$staged" "$target"; then
  [ "$had_old" -eq 0 ] || /bin/mv "$backup" "$target"
  fail
fi
if ! /usr/bin/open "$target"; then
  /bin/mv "$target" "$staged"
  [ "$had_old" -eq 0 ] || /bin/mv "$backup" "$target"
  /usr/bin/open "$target"
  fail
fi
"""

WINDOWS_HELPER = r"""param([int]$ParentPid, [string]$Installer, [string]$AppPath)
$ErrorActionPreference = 'Stop'
try {
  $deadline = (Get-Date).AddMinutes(2)
  while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {
    if ((Get-Date) -gt $deadline) { throw 'App did not close' }
    Start-Sleep -Seconds 1
  }
  $directory = [System.IO.Path]::GetDirectoryName($AppPath)
  $arguments = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="' + $directory + '"'
  $result = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
  if ($result.ExitCode -ne 0) { throw ('Installer failed: ' + $result.ExitCode) }
  Start-Process -FilePath $AppPath
} catch {
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.MessageBox]::Show('Update failed. Please reopen Keyframe Studio and try again.')
  exit 1
}
"""

def mac_app_path(executable=None):
    for parent in Path(executable or sys.executable).resolve().parents:
        if parent.suffix == ".app":
            return parent
    raise ValueError("Hãy cài bản .app trong Applications trước khi cập nhật")

def launch_installer(installer):
    """Return after preparing the detached installer; caller can now close Tk."""
    if not getattr(sys, "frozen", False):
        raise ValueError("Bản chạy từ source cần cập nhật bằng Git; hãy dùng bộ cài để cập nhật trong app")
    installer = Path(installer).resolve()
    work = installer.parent
    if sys.platform == "darwin":
        current = mac_app_path()
        target = current
        if str(current).startswith("/Volumes/"):
            target = Path.home() / "Applications" / current.name
            target.parent.mkdir(parents=True, exist_ok=True)
        if not os.access(target.parent, os.W_OK):
            raise PermissionError("Không có quyền ghi vào Applications. Hãy đặt app trong ~/Applications rồi thử lại.")
        mount = work / "mounted"
        mount.mkdir(exist_ok=True)
        staged = target.with_name("." + target.stem + ".update-" + uuid.uuid4().hex + ".app")
        backup = target.with_name("." + target.stem + ".previous-" + uuid.uuid4().hex + ".app")
        try:
            subprocess.run(["hdiutil", "attach", str(installer), "-nobrowse", "-readonly", "-mountpoint", str(mount)],
                           check=True, capture_output=True, timeout=90)
            source = mount / "CapCut Keyframe Studio.app"
            with (source / "Contents" / "Info.plist").open("rb") as stream:
                metadata = plistlib.load(stream)
            if metadata.get("CFBundleIdentifier") != "com.capcut.keyframestudio":
                raise ValueError("Bộ cài không đúng ứng dụng")
            subprocess.run(["ditto", str(source), str(staged)], check=True, capture_output=True, timeout=120)
        except Exception:
            shutil.rmtree(staged, ignore_errors=True)
            raise
        finally:
            subprocess.run(["hdiutil", "detach", str(mount)], capture_output=True, timeout=30)
        helper = work / "install.sh"
        helper.write_text(MAC_HELPER)
        log = (work / "install.log").open("ab")
        try:
            subprocess.Popen(["/bin/sh", str(helper), str(os.getpid()), str(target), str(staged), str(backup)],
                             stdout=log, stderr=log, start_new_session=True)
        except Exception:
            shutil.rmtree(staged, ignore_errors=True)
            raise
        finally:
            log.close()
    elif sys.platform == "win32":
        helper = work / "install.ps1"
        helper.write_text(WINDOWS_HELPER, encoding="utf-8-sig")
        subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                          "-File", str(helper), "-ParentPid", str(os.getpid()), "-Installer", str(installer),
                          "-AppPath", sys.executable], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        raise ValueError("Chưa hỗ trợ cập nhật tự động trên hệ điều hành này")
