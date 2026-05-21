import unittest

from spork.arch import normalize_arch, select_architecture


class ArchitectureSelectionTest(unittest.TestCase):
    def test_normalizes_common_machine_names(self) -> None:
        self.assertEqual(normalize_arch("x86_64"), "amd64")
        self.assertEqual(normalize_arch("aarch64"), "arm64")
        self.assertEqual(normalize_arch("armv7l"), "armhf")

    def test_selects_matching_architecture_variant(self) -> None:
        app = {
            "id": "demo",
            "architectures": {
                "amd64": {"url": "https://example.com/demo-amd64.deb"},
                "arm64": {"url": "https://example.com/demo-arm64.deb"},
            },
        }

        selected = select_architecture(app, "aarch64")

        self.assertIsNotNone(selected)
        data, arch = selected
        self.assertEqual(arch, "arm64")
        self.assertEqual(data["arch"], "arm64")
        self.assertEqual(data["url"], "https://example.com/demo-arm64.deb")
        self.assertNotIn("architectures", data)

    def test_returns_none_for_unsupported_architecture(self) -> None:
        app = {
            "id": "demo",
            "architectures": {
                "amd64": {"url": "https://example.com/demo-amd64.deb"},
            },
        }

        self.assertIsNone(select_architecture(app, "riscv64"))

    def test_arch_list_is_normalized_to_selected_string(self) -> None:
        app = {"id": "demo", "arch": ["x86_64", "aarch64"], "url": "https://example.com/demo.deb"}

        selected = select_architecture(app, "arm64")

        self.assertIsNotNone(selected)
        data, arch = selected
        self.assertEqual(arch, "arm64")
        self.assertEqual(data["arch"], "arm64")


if __name__ == "__main__":
    unittest.main()
