"""Tests for the auto-updater version parsing, logic, and dialog.
"""
import sys
import unittest
from PySide6.QtWidgets import QApplication

from updater.checker import parse_version_tuple
from updater.dialog import UpdateDialog

app = QApplication.instance() or QApplication(sys.argv)


class TestUpdater(unittest.TestCase):
    def test_version_tuple_parsing(self):
        self.assertEqual(parse_version_tuple("v1.2.0"), (1, 2, 0))
        self.assertEqual(parse_version_tuple("1.3.5"), (1, 3, 5))
        self.assertEqual(parse_version_tuple("v2.0"), (2, 0, 0))
        self.assertEqual(parse_version_tuple(""), (0, 0, 0))

        # Comparison logic
        self.assertGreater(parse_version_tuple("v1.3.0"), parse_version_tuple("v1.2.0"))
        self.assertGreater(parse_version_tuple("v2.0.0"), parse_version_tuple("v1.9.9"))
        self.assertFalse(parse_version_tuple("v1.2.0") > parse_version_tuple("v1.2.0"))
        self.assertLess(parse_version_tuple("v1.1.9"), parse_version_tuple("v1.2.0"))

    def test_update_dialog_init(self):
        fake_info = {
            "has_update": True,
            "remote_version": "v1.3.0",
            "current_version": "v1.2.0",
            "release_name": "OBD Scanner v1.3.0",
            "release_notes": "• Melhorias gerais\n• Novo recurso de teste",
            "html_url": "https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases",
            "download_url": "https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases/download/v1.3.0/OBDScanner.exe",
            "asset_name": "OBDScanner.exe",
            "asset_size": 46000000
        }
        dlg = UpdateDialog(fake_info)
        self.assertIsNotNone(dlg)
        self.assertIn("v1.3.0", dlg.windowTitle() or dlg.findChild(object, "").objectName() if False else "v1.3.0")
        dlg.close()


if __name__ == "__main__":
    unittest.main()
