"""Comprehensive test suite for OBD Scanner core modules.
"""
import unittest
import os
import tempfile

from obd.parser import decode_single_dtc, clean_hex_stream, parse_dtc_response
from dtc.database import get_dtc_info
from dtc.advisor import DiagnosticAdvisor
from dtc.reader import DTCReader
from database.db import DiagnosticDatabase
from reports.generator import ReportGenerator
from elm327.mock_adapter import MockELM327Connection


class TestOBDParser(unittest.TestCase):
    def test_decode_dtc(self):
        # 0x01, 0x06 -> P0106
        self.assertEqual(decode_single_dtc(0x01, 0x06), "P0106")
        # 0x03, 0x00 -> P0300
        self.assertEqual(decode_single_dtc(0x03, 0x00), "P0300")
        # 0x04, 0x20 -> P0420
        self.assertEqual(decode_single_dtc(0x04, 0x20), "P0420")
        # 0x00, 0x00 -> None (padding)
        self.assertIsNone(decode_single_dtc(0x00, 0x00))

    def test_parse_single_frame_dtc(self):
        raw = "43 01 06 03 00 00 00"
        dtcs = parse_dtc_response(raw, "43")
        self.assertEqual(dtcs, ["P0106", "P0300"])

    def test_parse_no_data(self):
        self.assertEqual(parse_dtc_response("NO DATA", "43"), [])
        self.assertEqual(parse_dtc_response("UNABLE TO CONNECT", "43"), [])

    def test_parse_can_multiframe(self):
        raw = """
        0: 43 04 01 06 03 00
        1: 00 01 30 04 20 00
        """
        dtcs = parse_dtc_response(raw, "43")
        self.assertIn("P0106", dtcs)
        self.assertIn("P0300", dtcs)


class TestDTCDatabaseAndAdvisor(unittest.TestCase):
    def test_dtc_catalog(self):
        meta_p0106 = get_dtc_info("P0106")
        self.assertIn("MAP", meta_p0106.description)
        self.assertTrue(len(meta_p0106.checklist) > 0)

        # Generic code fallback
        meta_generic = get_dtc_info("P0999")
        self.assertEqual(meta_generic.code, "P0999")
        self.assertTrue("Trem de Força" in meta_generic.system)

    def test_advisor_correlations(self):
        corrs = DiagnosticAdvisor.analyze_correlations(["P0106", "P0300"])
        self.assertTrue(len(corrs) >= 1)
        self.assertIn("Pressão do Coletor", corrs[0]["title"])
        self.assertIn("Combustão", corrs[0]["title"])


class TestMockConnectionAndDTCReader(unittest.TestCase):
    def test_mock_flow(self):
        conn = MockELM327Connection()
        ok_conn, _ = conn.connect()
        self.assertTrue(ok_conn)

        ok_init, _ = conn.initialize_elm()
        self.assertTrue(ok_init)
        self.assertEqual(conn.battery_voltage, "12.6V")

        ok_ecu, _ = conn.test_ecu_communication()
        self.assertTrue(ok_ecu)
        self.assertTrue(conn.ecu_connected)

        reader = DTCReader(conn)
        items, msg = reader.read_all_dtcs()
        codes = [i.code for i in items]
        self.assertIn("P0106", codes)
        self.assertIn("P0300", codes)
        self.assertIn("P0130", codes)


class TestDatabaseAndReports(unittest.TestCase):
    def test_sqlite_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            test_db = DiagnosticDatabase(temp_db_path)
            session_id = test_db.save_session(
                vehicle_name="Renault Logan 2018 1.0",
                port="COM3",
                baudrate=38400,
                elm_version="ELM327 v1.5",
                protocol_name="ISO 15765-4 CAN",
                battery_voltage="12.6V",
                stored_codes=["P0106", "P0300"],
                pending_codes=["P0130"],
                permanent_codes=[],
                advisor_notes="Teste de notas",
                raw_log="ATZ\nOK"
            )
            self.assertGreater(session_id, 0)

            sessions = test_db.list_sessions()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["stored_codes"], ["P0106", "P0300"])

            sess = test_db.get_session(session_id)
            self.assertIsNotNone(sess)
            self.assertEqual(sess["vehicle_name"], "Renault Logan 2018 1.0")

            test_db.delete_session(session_id)
            self.assertEqual(len(test_db.list_sessions()), 0)
        finally:
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

    def test_report_generation(self):
        conn = MockELM327Connection()
        conn.connect()
        reader = DTCReader(conn)
        items, _ = reader.read_all_dtcs()
        correlations = DiagnosticAdvisor.analyze_correlations([i.code for i in items])

        html = ReportGenerator.generate_html(
            vehicle_name="Renault Logan 2018 1.0",
            port="COM3",
            elm_version="ELM327 v1.5",
            protocol="ISO 15765-4 CAN",
            voltage="12.6V",
            dtc_items=items,
            correlations=correlations,
            raw_log="ATZ\nOK\n0100\n41 00 BE 3F"
        )
        self.assertIn("Renault Logan 2018 1.0", html)
        self.assertIn("P0106", html)

        txt = ReportGenerator.generate_txt(
            vehicle_name="Renault Logan 2018 1.0",
            port="COM3",
            elm_version="ELM327 v1.5",
            protocol="ISO 15765-4 CAN",
            voltage="12.6V",
            dtc_items=items,
            correlations=correlations,
            raw_log="ATZ\nOK\n0100\n41 00 BE 3F"
        )
        self.assertIn("RELATÓRIO DE DIAGNÓSTICO OBD2", txt)
        self.assertIn("P0106", txt)


if __name__ == "__main__":
    unittest.main()
