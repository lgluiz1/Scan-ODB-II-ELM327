"""Headless test for GUI initialization and signals.
"""
import sys
import unittest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)

class TestGUI(unittest.TestCase):
    def test_window_init(self):
        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual(win.tabs.count(), 8)
        self.assertFalse(win.btn_read_dtc.isEnabled())
        self.assertFalse(win.btn_clear_dtc.isEnabled())

        # Test simulation port selection and state
        idx = win.combo_ports.findData("MOCK")
        self.assertGreaterEqual(idx, 0)
        win.combo_ports.setCurrentIndex(idx)

        # Trigger mock connect and test UI reaction
        win._handle_connect()
        win.worker.wait(5000)
        app.processEvents()

        # After worker finishes, verify connected state
        self.assertIsNotNone(win.conn)
        self.assertTrue(win.conn.is_connected)
        self.assertTrue(win.btn_read_dtc.isEnabled())
        self.assertTrue(win.btn_clear_dtc.isEnabled())
        self.assertEqual(win.badge_elm.title_text, "Adaptador ELM327")

        # Test reading DTCs
        win._handle_read_dtcs()
        win.worker.wait(5000)
        app.processEvents()

        self.assertGreater(len(win.current_dtcs), 0)
        self.assertTrue(win.btn_export_report.isEnabled())

        # Test Mode 04 Clear DTCs
        from dtc.reader import DTCReader
        reader = DTCReader(win.conn)
        ok_clear, msg_clear = reader.clear_all_dtcs()
        self.assertTrue(ok_clear)

        # Test re-read after clear
        items_after, _ = reader.read_all_dtcs()
        self.assertEqual(len(items_after), 0)

        # Disconnect
        win._handle_disconnect()
        self.assertIsNone(win.conn)
        self.assertFalse(win.btn_read_dtc.isEnabled())
        self.assertFalse(win.btn_clear_dtc.isEnabled())

        win.close()


if __name__ == "__main__":
    unittest.main()
