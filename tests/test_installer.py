import os
import tempfile
import unittest
from unittest.mock import patch

from spork.installer import install
from spork.state import get_installed


class InstallStateTest(unittest.TestCase):
    def test_install_imports_existing_older_system_package(self) -> None:
        app = {
            "id": "demo",
            "package": "demo-package",
            "name": "Demo",
            "version": "2.0.0",
            "arch": "amd64",
            "bucket": "main",
            "url": "https://example.com/demo.deb",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_home = os.environ.get("SPORK_HOME")
            os.environ["SPORK_HOME"] = temp_dir
            try:
                with (
                    patch("spork.installer.find_app", return_value=app),
                    patch("spork.installer.dpkg.installed_version", return_value="1.0.0"),
                    patch("spork.installer.dpkg.compare_versions", return_value=True),
                    patch("spork.installer.download") as download,
                    patch("spork.installer.system_packages.install_file") as install_file,
                ):
                    install("demo", yes=True)

                record = get_installed("demo")
                self.assertIsNotNone(record)
                self.assertEqual(record["version"], "1.0.0")
                self.assertEqual(record["lastAction"], "import")
                download.assert_not_called()
                install_file.assert_not_called()
            finally:
                if previous_home is None:
                    os.environ.pop("SPORK_HOME", None)
                else:
                    os.environ["SPORK_HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
