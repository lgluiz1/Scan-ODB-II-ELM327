import unittest
import sys
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from ui.widgets.lambda_view import LambdaView, O2OscilloscopeWidget
from elm327.mock_adapter import MockELM327Connection


class TestLambdaView(unittest.TestCase):
    def test_oscilloscope_widget(self):
        osc = O2OscilloscopeWidget()
        osc.resize(600, 300)
        # Add sample data
        osc.add_sample(0.75, 0.58)
        osc.add_sample(0.22, 0.60)
        self.assertEqual(len(osc.data_history), 2)
        osc.clear_data()
        self.assertEqual(len(osc.data_history), 0)

    def test_lambda_view_logic(self):
        lv = LambdaView()
        self.assertIsNotNone(lv)

        conn = MockELM327Connection()
        conn.connect()
        conn.initialize_elm()
        lv.set_connection(conn)

        # Simulate receiving samples
        for i in range(25):
            v1 = 0.80 if i % 2 == 0 else 0.15
            v2 = 0.58 + (i * 0.002)
            lv._on_sample_received(v1, v2, 1.000)

        # Check that cards updated
        s1_val = lv.card_s1.findChild(object, "cardVal").text()
        s2_val = lv.card_s2.findChild(object, "cardVal").text()
        diag_val = lv.card_diag.findChild(object, "cardVal").text()

        self.assertIn("V", s1_val)
        self.assertIn("V", s2_val)
        self.assertEqual(diag_val, "CATALISADOR SAUDÁVEL")

        lv.stop_monitoring()


if __name__ == "__main__":
    unittest.main()
