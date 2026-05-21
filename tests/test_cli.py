import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from spork.cli import main


class ListCommandTest(unittest.TestCase):
    def test_list_defaults_to_installed_apps(self) -> None:
        installed = [
            {
                "id": "demo",
                "name": "Demo",
                "package": "demo-package",
                "version": "1.0.0",
                "bucket": "main",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_home = os.environ.get("SPORK_HOME")
            os.environ["SPORK_HOME"] = temp_dir
            try:
                stdout = io.StringIO()
                with (
                    patch("spork.cli.list_installed", return_value=installed) as list_installed,
                    patch("spork.cli.all_apps", return_value=[]) as all_apps,
                    contextlib.redirect_stdout(stdout),
                ):
                    exit_code = main(["list"])

                self.assertEqual(exit_code, 0)
                list_installed.assert_called_once_with()
                all_apps.assert_not_called()
                self.assertIn("demo", stdout.getvalue())
            finally:
                if previous_home is None:
                    os.environ.pop("SPORK_HOME", None)
                else:
                    os.environ["SPORK_HOME"] = previous_home

    def test_list_available_shows_index_apps(self) -> None:
        available = [
            {
                "id": "demo",
                "name": "Demo",
                "package": "demo-package",
                "version": "2.0.0",
                "bucket": "main",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_home = os.environ.get("SPORK_HOME")
            os.environ["SPORK_HOME"] = temp_dir
            try:
                stdout = io.StringIO()
                with (
                    patch("spork.cli.list_installed", return_value=[]) as list_installed,
                    patch("spork.cli.all_apps", return_value=available) as all_apps,
                    contextlib.redirect_stdout(stdout),
                ):
                    exit_code = main(["list", "--available"])

                self.assertEqual(exit_code, 0)
                all_apps.assert_called_once_with()
                list_installed.assert_not_called()
                self.assertIn("demo", stdout.getvalue())
            finally:
                if previous_home is None:
                    os.environ.pop("SPORK_HOME", None)
                else:
                    os.environ["SPORK_HOME"] = previous_home


if __name__ == "__main__":
    unittest.main()
