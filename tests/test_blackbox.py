"""Automated test suite for Blackbox (Modo Viagem) continuous monitoring.
"""
import unittest
import os
import shutil
import tempfile
import time

from obd.pids import parse_pid_support_bitmap, decode_pid_value
from blackbox.config import BlackboxConfig
from blackbox.models import SampleData, TripEvent, TripMetadata
from blackbox.trip_manager import TripManager
from blackbox.recovery import CrashRecovery
from elm327.mock_adapter import MockELM327Connection
from database.db import DiagnosticDatabase


class TestOBDPids(unittest.TestCase):
    def test_support_bitmap(self):
        # 41 00 BE 3F B8 10
        raw = "41 00 BE 3F B8 10"
        supported = parse_pid_support_bitmap(raw, base_pid=0)
        self.assertIn("010C", supported)  # RPM
        self.assertIn("010D", supported)  # SPEED
        self.assertIn("010B", supported)  # MAP
        self.assertIn("0104", supported)  # LOAD
        self.assertIn("0105", supported)  # ECT

    def test_decode_pids(self):
        # RPM: ((15 * 256) + 160) / 4 = (3840 + 160) / 4 = 1000 rpm
        val_rpm = decode_pid_value("010C", "41 0C 0F A0")
        self.assertEqual(val_rpm, 1000)

        # MAP: 0x28 = 40 kPa
        val_map = decode_pid_value("010B", "41 0B 28")
        self.assertEqual(val_map, 40)

        # ECT: 0x7F = 127 - 40 = 87 °C
        val_ect = decode_pid_value("0105", "41 05 7F")
        self.assertEqual(val_ect, 87)

        # STFT: 0x80 = 128 -> (128 - 128) * 100 / 128 = 0.0 %
        val_stft = decode_pid_value("0106", "41 06 80")
        self.assertEqual(val_stft, 0.0)


class TestTripManagerAndEventBuffer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = BlackboxConfig(
            pre_event_seconds=5,    # Short test windows
            post_event_seconds=2,
            storage_dir=self.test_dir
        )
        self.manager = TripManager(self.config)

    def tearDown(self):
        if self.manager._csv_file and not self.manager._csv_file.closed:
            self.manager._csv_file.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_trip_lifecycle_and_buffers(self):
        # 1. Start trip
        trip = self.manager.start_trip(
            port="COM3",
            elm_version="ELM327 v1.5",
            protocol_name="ISO 15765-4 CAN",
            supported_pids=["010C", "010B"]
        )
        self.assertTrue(os.path.exists(trip.folder_path))
        self.assertTrue(os.path.exists(os.path.join(trip.folder_path, "dados.csv")))
        self.assertTrue(os.path.exists(os.path.join(trip.folder_path, "viagem.json")))

        # 2. Add continuous samples
        start_mono = time.monotonic()
        for i in range(10):
            sample = SampleData(
                timestamp=f"2026-10-06 08:35:{i:02d}",
                monotonic_ts=start_mono + i,
                values={"RPM": 1500 + i * 10, "MAP": 40 + i, "SPEED": 50}
            )
            self.manager.add_sample(sample)

        # Rolling buffer should have samples
        self.assertGreater(len(self.manager.rolling_buffer), 0)

        # 3. Trigger confirmed DTC event (P0300)
        event = self.manager.trigger_event(
            event_type="DTC",
            code="P0300",
            title="Falha de Combustão Detectada",
            description="Misfire registrado sob carga"
        )
        self.assertEqual(len(self.manager.active_events), 1)
        self.assertEqual(event.code, "P0300")
        self.assertGreater(len(event.pre_samples), 0)

        # 4. Add post-event samples until post_event_seconds is satisfied
        for i in range(10, 15):
            sample = SampleData(
                timestamp=f"2026-10-06 08:35:{i:02d}",
                monotonic_ts=start_mono + i + 5,
                values={"RPM": 1400, "MAP": 50, "SPEED": 40}
            )
            self.manager.add_sample(sample)

        # Active events should now be completed and finalized to disk
        self.assertEqual(len(self.manager.active_events), 0)
        self.assertEqual(len(self.manager.completed_events), 1)

        # Verify files generated in event folder
        completed_ev = self.manager.completed_events[0]
        self.assertTrue(os.path.exists(completed_ev.folder_path))
        self.assertTrue(os.path.exists(os.path.join(completed_ev.folder_path, "evento.json")))
        self.assertTrue(os.path.exists(os.path.join(completed_ev.folder_path, "dados.csv")))
        self.assertTrue(os.path.exists(os.path.join(completed_ev.folder_path, "relatorio.html")))

        # 5. Stop trip
        final_trip = self.manager.stop_trip()
        self.assertEqual(final_trip.status, "FINALIZADA")
        self.assertEqual(final_trip.events_count, 1)
        self.assertEqual(final_trip.dtc_count, 1)

    def test_crash_recovery(self):
        # Create unfinalized trip
        trip = self.manager.start_trip("COM3", "ELM327", "CAN", [])
        incomplete = CrashRecovery.find_incomplete_trips(self.test_dir)
        self.assertEqual(len(incomplete), 1)
        self.assertEqual(incomplete[0]["trip_id"], trip.trip_id)

    def test_trip_simulation_scenario(self):
        # Test simulated trip with MockELM327Connection
        conn = MockELM327Connection()
        conn.scenario_mode = "TRIP_SIMULATION"
        conn.connect()
        conn.initialize_elm()

        trip = self.manager.start_trip("MOCK", "ELM327 v1.5", "CAN", ["010C", "010B", "0111", "0104", "0106"])

        # Run 20 cycles: should advance from cruise to hill climb and trigger P0300
        for i in range(25):
            conn.send_raw_command("010C")  # Advances cycle count
            raw_map = conn.send_raw_command("010B")[1]
            raw_rpm = conn.send_raw_command("010C")[1]
            raw_dtc = conn.send_raw_command("03")[1]

            sample = SampleData(
                timestamp=f"2026-10-06 08:35:{i:02d}",
                monotonic_ts=time.monotonic() + i,
                values={"RPM": 1400, "MAP": 90, "TPS": 65}
            )
            self.manager.add_sample(sample)

            if "03 00" in raw_dtc and len(self.manager.active_events) == 0 and len(self.manager.completed_events) == 0:
                self.manager.trigger_event("DTC", "P0300", "Misfire Detectado", "Falha de combustão sob carga")

        # Now simulate post-event samples
        for i in range(25, 30):
            sample = SampleData(
                timestamp=f"2026-10-06 08:35:{i:02d}",
                monotonic_ts=time.monotonic() + i + 10,
                values={"RPM": 1800, "MAP": 45, "TPS": 25}
            )
            self.manager.add_sample(sample)

        # Event should now be completed and saved
        self.assertEqual(len(self.manager.completed_events), 1)
        ev = self.manager.completed_events[0]
        self.assertEqual(ev.code, "P0300")
        self.assertTrue(os.path.exists(os.path.join(ev.folder_path, "evento.json")))
        self.assertTrue(os.path.exists(os.path.join(ev.folder_path, "dados.csv")))

        self.manager.stop_trip()


if __name__ == "__main__":
    unittest.main()
