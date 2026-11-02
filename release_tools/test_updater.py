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

if __name__ == "__main__":
    unittest.main()
