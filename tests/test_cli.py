import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from spork.cli import main


class HelpCommandTest(unittest.TestCase):
    def test_no_arguments_prints_help_like_dash_h(self) -> None:
        def run_cli(argv: list[str]) -> tuple[int, str]:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                try:
                    exit_code = main(argv)
                except SystemExit as exc:
                    exit_code = int(exc.code or 0)
            return exit_code, stdout.getvalue()

        no_args_exit_code, no_args_output = run_cli([])
        help_exit_code, help_output = run_cli(["-h"])

        self.assertEqual(no_args_exit_code, 0)
        self.assertEqual(help_exit_code, 0)
        self.assertEqual(no_args_output, help_output)

    def test_purge_is_not_a_top_level_command(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                exit_code = main(["-h"])
            except SystemExit as exc:
                exit_code = int(exc.code or 0)

        self.assertEqual(exit_code, 0)
        self.assertNotIn("purge", stdout.getvalue())
        self.assertNotIn("autoremove", stdout.getvalue())

    def test_uninstall_help_places_app_id_before_options(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                exit_code = main(["uninstall", "-h"])
            except SystemExit as exc:
                exit_code = int(exc.code or 0)

        self.assertEqual(exit_code, 0)
        self.assertIn("usage: spork uninstall <app-id> [-y] [--package PACKAGE] [--purge] [--autoremove]", stdout.getvalue())


class UninstallCommandTest(unittest.TestCase):
    def test_uninstall_purge_passes_purge_option(self) -> None:
        with (
            patch("spork.cli.ensure_initial_files"),
            patch("spork.cli.load_config", return_value={}),
            patch("spork.cli.set_language"),
            patch("spork.cli.remove") as remove,
        ):
            exit_code = main(["uninstall", "demo", "--purge", "-y"])

        self.assertEqual(exit_code, 0)
        remove.assert_called_once_with("demo", yes=True, package=None, purge=True)

    def test_uninstall_autoremove_runs_after_successful_remove(self) -> None:
        with (
            patch("spork.cli.ensure_initial_files"),
            patch("spork.cli.load_config", return_value={}),
            patch("spork.cli.set_language"),
            patch("spork.cli.remove", return_value=True) as remove,
            patch("spork.cli.autoremove") as autoremove,
        ):
            exit_code = main(["uninstall", "demo", "--autoremove", "-y"])

        self.assertEqual(exit_code, 0)
        remove.assert_called_once_with("demo", yes=True, package=None, purge=False)
        autoremove.assert_called_once_with(yes=True)


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
