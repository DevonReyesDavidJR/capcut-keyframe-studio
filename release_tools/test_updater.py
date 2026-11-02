"""Updater tests use a fake release server and never replace an installed app."""
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import updater

class UpdaterTests(unittest.TestCase):
    def release(self, version="v0.2.0-preview.4", prerelease=True, arch="arm64"):
        name = updater.asset_name("Darwin", arch)
        base = "https://github.com/" + updater.REPOSITORY + "/releases/download/" + version + "/"
        return {"tag_name": version, "draft": False, "prerelease": prerelease, "body": "Notes",
                "assets": [{"name": name, "size": 7, "browser_download_url": base + name},
                           {"name": "SHA256SUMS.txt", "browser_download_url": base + "SHA256SUMS.txt"}]}

    def test_versions_and_platforms(self):
        self.assertGreater(updater.version_key("0.2.0-preview.10"), updater.version_key("0.2.0-preview.2"))
        self.assertGreater(updater.version_key("0.2.0"), updater.version_key("0.2.0-preview.99"))
        self.assertIn("arm64", updater.asset_name("Darwin", "aarch64"))
        self.assertIn("x86_64", updater.asset_name("Darwin", "x86_64"))
        self.assertTrue(updater.asset_name("Windows", "AMD64").endswith(".exe"))
        with self.assertRaises(ValueError): updater.asset_name("Windows", "ARM64")
        with self.assertRaises(ValueError): updater.version_key("latest")

    def test_release_selection(self):
        releases = [self.release("v0.2.0-preview.10"), self.release("v0.2.0-preview.4")]
        result = updater.find_update("0.2.0-preview.3", releases=releases, system="Darwin", machine="arm64")
        self.assertEqual(result["version"], "0.2.0-preview.10")
        self.assertIsNone(updater.find_update("0.2.0", releases=releases, system="Darwin", machine="arm64"))
        self.assertIsNone(updater.find_update("0.2.0-preview.10", releases=releases, system="Darwin", machine="arm64"))
        releases[0]["draft"] = True
        releases[1]["assets"][0]["browser_download_url"] = "https://example.com/malware.dmg"
        self.assertIsNone(updater.find_update("0.2.0-preview.3", releases=releases, system="Darwin", machine="arm64"))

    def update(self):
        return updater.find_update("0.2.0-preview.3", releases=[self.release()], system="Darwin", machine="arm64")

    def test_verified_download(self):
        update = self.update()
        data = b"package"
        manifest = hashlib.sha256(data).hexdigest() + "  " + update["asset"]["name"]
        values = []
        with patch.object(updater, "_read", return_value=manifest.encode()), patch.object(updater, "_open", return_value=io.BytesIO(data)):
            path = updater.download(update, progress=values.append)
        try:
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(values[-1], 100)
        finally:
            shutil.rmtree(path.parent)

    def test_corrupt_and_cancelled_downloads_are_removed(self):
        update = self.update()
        manifest = "0" * 64 + "  " + update["asset"]["name"]
        for cancel in (False, True):
            directory = Path(tempfile.mkdtemp())
            with patch.object(updater.tempfile, "mkdtemp", return_value=str(directory)), patch.object(updater, "_read", return_value=manifest.encode()), patch.object(updater, "_open", return_value=io.BytesIO(b"package")):
                with self.assertRaises((ValueError, RuntimeError)):
                    updater.download(update, cancelled=lambda: cancel)
            self.assertFalse(directory.exists())

    def test_checksum_names_and_origin(self):
        with self.assertRaises(ValueError): updater.checksum_for("0" * 64 + "  another.dmg", "app.dmg")
        self.assertFalse(updater.trusted_asset("https://github.com.evil.test/" + updater.REPOSITORY + "/releases/download/v1/app.dmg"))
        self.assertFalse(updater.trusted_asset("http://github.com/" + updater.REPOSITORY + "/releases/download/v1/app.dmg"))
        self.assertFalse(updater.trusted_asset("https://github.com/another/repo/releases/download/v1/app.dmg"))

    def test_installer_requires_packaged_app(self):
        with patch.object(updater.sys, "frozen", False, create=True):
            with self.assertRaises(ValueError): updater.launch_installer(Path("fake.dmg"))

    def test_mac_app_detection_and_helper_syntax(self):
        self.assertEqual(updater.mac_app_path("/Applications/Keyframe Studio.app/Contents/MacOS/app"),
                         Path("/Applications/Keyframe Studio.app"))
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "install.sh"
            helper.write_text(updater.MAC_HELPER)
            subprocess.run(["sh", "-n", str(helper)], check=True)

    def test_windows_handoff_does_not_run_installer_in_process(self):
        with tempfile.TemporaryDirectory() as directory:
            installer = Path(directory) / "setup.exe"
            installer.write_bytes(b"fixture")
            with patch.object(updater.sys, "frozen", True, create=True), patch.object(updater.sys, "platform", "win32"), patch.object(updater.subprocess, "CREATE_NO_WINDOW", 0, create=True), patch.object(updater.subprocess, "Popen") as process:
                updater.launch_installer(installer)
                args = process.call_args.args[0]
                self.assertEqual(args[0], "powershell.exe")
                self.assertIn(str(installer), args)
                self.assertIn("-ParentPid", args)
                self.assertTrue((Path(directory) / "install.ps1").exists())


    def test_mac_helper_replaces_atomically_and_rolls_back(self):
        for open_success, stage_exists in ((True, True), (False, True), (True, False)):
            with tempfile.TemporaryDirectory(prefix="update test ") as directory:
                root = Path(directory)
                target, staged, backup = root / "Studio app.app", root / "staged.app", root / "backup.app"
                target.mkdir()
                (target / "version").write_text("old")
                if stage_exists:
                    staged.mkdir()
                    (staged / "version").write_text("new")
                script = updater.MAC_HELPER.replace('/usr/bin/open "$target"', '/usr/bin/true' if open_success else '/usr/bin/false')
                script = script.replace('/usr/bin/osascript -e', ':')
                helper = root / "install.sh"
                helper.write_text(script)
                result = subprocess.run(["sh", str(helper), "99999999", str(target), str(staged), str(backup)], capture_output=True, timeout=10)
                if open_success and stage_exists:
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual((target / "version").read_text(), "new")
                    self.assertEqual((backup / "version").read_text(), "old")
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual((target / "version").read_text(), "old")

    def test_mac_preparation_checks_identity_before_handoff(self):
        import plistlib
        for valid in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / "Installed app.app"
                target.mkdir()
                (target / "old").touch()
                installer = root / "update.dmg"
                installer.touch()
                def run(args, **kwargs):
                    if args[0] == "hdiutil" and args[1] == "attach":
                        source = root / "mounted" / "CapCut Keyframe Studio.app" / "Contents"
                        source.mkdir(parents=True)
                        with (source / "Info.plist").open("wb") as stream:
                            plistlib.dump({"CFBundleIdentifier": "com.capcut.keyframestudio" if valid else "wrong.app"}, stream)
                    if args[0] == "ditto":
                        shutil.copytree(args[1], args[2])
                with patch.object(updater.sys, "frozen", True, create=True), patch.object(updater.sys, "platform", "darwin"), patch.object(updater, "mac_app_path", return_value=target), patch.object(updater.subprocess, "run", side_effect=run), patch.object(updater.subprocess, "Popen") as launch:
                    if valid:
                        updater.launch_installer(installer)
                        self.assertEqual(launch.call_args.args[0][0], "/bin/sh")
                    else:
                        with self.assertRaises(ValueError): updater.launch_installer(installer)
                        launch.assert_not_called()
                self.assertTrue((target / "old").exists())

if __name__ == "__main__":
    unittest.main()
