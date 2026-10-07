"""Continuous background monitor thread for Blackbox telemetry acquisition and event detection.
"""
import time
import datetime
from typing import Dict, Any, List, Set, Optional

from PySide6.QtCore import QThread, Signal

from blackbox.config import BlackboxConfig
from blackbox.models import SampleData, TripEvent, TripMetadata
from blackbox.trip_manager import TripManager
from obd.pids import PID_CATALOG, parse_pid_support_bitmap, decode_pid_value
from obd.parser import parse_dtc_response
from utils.logger import tech_logger


class TripMonitor(QThread):
    """
    Acquires real-time OBD2 telemetry in a dedicated background thread.
    Executes adaptive scheduling, anomaly detection, DTC checking, and auto-reconnection.
    """
    # Signals for UI update
    sample_recorded = Signal(object)           # SampleData
    event_detected = Signal(object)            # TripEvent
    status_updated = Signal(dict)              # {'elm': str, 'ecu': str, 'engine': str, 'cycle_ms': int, 'dtc_count': int, 'events_count': int}
    trip_finished = Signal(object)             # TripMetadata
    error_occurred = Signal(str)

    def __init__(self, connection, trip_manager: TripManager, config: Optional[BlackboxConfig] = None):
        super().__init__()
        self.conn = connection
        self.manager = trip_manager
        self.config = config or BlackboxConfig()

        self._running = False
        self._paused = False

        # Monitored PIDs list
        self.supported_pids: List[str] = []
        self.priority_pids = [
            "010C",  # RPM
            "010D",  # SPEED
            "010B",  # MAP
            "0111",  # TPS
            "0104",  # LOAD
            "0105",  # ECT
            "0106",  # STFT
            "0107",  # LTFT
            "0114",  # O2 S1
            "010E",  # TIMING
            "0110",  # MAF
        ]

        # Engine state
        self.engine_state = "DESCONHECIDO"  # "FUNCIONANDO", "PARADO", "ECU_OFF"
        self.consecutive_errors = 0

        # DTC Tracking and cooldown
        self.known_dtcs: Set[str] = set()
        self.last_dtc_check_mono = 0.0
        self.dtc_check_interval = 12.0  # seconds between routine DTC checks

        # Anomaly tracking
        self.last_sample: Optional[SampleData] = None
        self.last_suspicious_mono = 0.0

    def run(self):
        self._running = True
        tech_logger.info("[CAIXA-PRETA] Iniciando thread de monitoramento contínuo...")

        try:
            # 1. Discover Supported PIDs
            self._discover_supported_pids()

            # 2. Main acquisition loop
            while self._running:
                if self._paused:
                    time.sleep(0.2)
                    continue

                cycle_start = time.monotonic()

                # Verify connection health
                if not self.conn or not self.conn.is_connected:
                    self._handle_disconnection()
                    continue

                # Telemetry cycle
                sample = self._acquire_cycle()

                if sample:
                    self.consecutive_errors = 0
                    self.manager.add_sample(sample)
                    self.sample_recorded.emit(sample)

                    # Check for anomalies
                    if self.config.detect_suspicious_events:
                        self._check_suspicious_anomalies(sample)

                    self.last_sample = sample
                else:
                    self.consecutive_errors += 1
                    max_timeouts = getattr(self.config, 'anomaly_consecutive_timeouts', 3)
                    if self.consecutive_errors >= max_timeouts:
                        self._on_consecutive_timeouts()

                # Check DTCs periodically
                now_mono = time.monotonic()
                if now_mono - self.last_dtc_check_mono >= self.dtc_check_interval:
                    self._check_dtcs()
                    self.last_dtc_check_mono = now_mono

                # Measure cycle duration and calculate adaptive sleep
                cycle_duration_ms = int((time.monotonic() - cycle_start) * 1000)
                target_cycle_ms = max(self.config.adaptive_min_ms, min(self.config.adaptive_max_ms, cycle_duration_ms + 100))
                sleep_needed = max(0.02, (target_cycle_ms - cycle_duration_ms) / 1000.0)

                # Update UI status
                dtc_cnt = self.manager.current_trip.dtc_count if self.manager.current_trip else 0
                ev_cnt = self.manager.current_trip.events_count if self.manager.current_trip else 0
                self.status_updated.emit({
                    "elm": "CONECTADO" if (self.conn and self.conn.is_connected) else "DESCONECTADO",
                    "ecu": "CONECTADA" if (self.conn and self.conn.ecu_connected) else "SEM_RESPOSTA",
                    "engine": self.engine_state,
                    "cycle_ms": cycle_duration_ms,
                    "dtc_count": dtc_cnt,
                    "events_count": ev_cnt
                })

                time.sleep(sleep_needed)

        except Exception as e:
            tech_logger.error(f"[CAIXA-PRETA] Exceção na thread de monitoramento: {str(e)}")
            self.error_occurred.emit(str(e))
        finally:
            tech_logger.info("[CAIXA-PRETA] Thread de monitoramento encerrada.")

    def stop_monitoring(self):
        """Signals the thread to stop."""
        self._running = False
        self.wait(3000)

    def pause_monitoring(self, paused: bool):
        self._paused = paused

    def _discover_supported_pids(self):
        """Query 0100, 0120 to find available PIDs."""
        supported_set: Set[str] = set()

        ok, resp = self.conn.send_raw_command("0100", timeout=3.0)
        if ok and resp:
            s0 = parse_pid_support_bitmap(resp, base_pid=0)
            supported_set.update(s0)

        # Check PID 20 if supported
        if "0120" in supported_set:
            ok20, resp20 = self.conn.send_raw_command("0120", timeout=2.0)
            if ok20 and resp20:
                s20 = parse_pid_support_bitmap(resp20, base_pid=32)
                supported_set.update(s20)

        # Filter priority PIDs to only those actually supported
        self.supported_pids = [p for p in self.priority_pids if p in supported_set]
        if not self.supported_pids:
            # Fallback to core standard PIDs if ECU didn't provide standard 0100 bitmask
            self.supported_pids = ["010C", "010D", "010B", "0111", "0104", "0105", "0106", "0107"]

        tech_logger.info(f"[CAIXA-PRETA] PIDs suportados configurados para aquisição: {', '.join(self.supported_pids)}")

    def _acquire_cycle(self) -> Optional[SampleData]:
        """Queries the sequence of PIDs and builds a SampleData."""
        values: Dict[str, Any] = {}
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        now_mono = time.monotonic()

        success_count = 0
        for pid_hex in self.supported_pids:
            if not self._running or self._paused:
                break

            ok, resp = self.conn.send_raw_command(pid_hex, timeout=1.0)
            if ok and resp:
                val = decode_pid_value(pid_hex, resp)
                if val is not None:
                    name = PID_CATALOG[pid_hex].name
                    values[name] = val
                    success_count += 1

        if success_count == 0:
            return None

        # Update engine state
        rpm = values.get("RPM")
        if rpm is not None:
            if rpm > 300:
                self.engine_state = "FUNCIONANDO"
            else:
                self.engine_state = "PARADO"
        else:
            self.engine_state = "SEM_RPM"

        return SampleData(timestamp=now_str, monotonic_ts=now_mono, values=values)

    def _check_dtcs(self):
        """Lightweight query of Mode 03 & Mode 07 for newly triggered codes."""
        ok_03, resp_03 = self.conn.send_raw_command("03", timeout=2.0)
        current_dtcs: Set[str] = set()

        if ok_03 and resp_03:
            codes_03 = parse_dtc_response(resp_03, "43")
            current_dtcs.update(codes_03)

        # Check for new codes
        new_codes = current_dtcs - self.known_dtcs
        if new_codes:
            for code in new_codes:
                self._trigger_dtc_event(code)
            self.known_dtcs.update(new_codes)

        # Remove cleared codes so they can re-trigger if they return later
        cleared_codes = self.known_dtcs - current_dtcs
        if cleared_codes:
            for c in cleared_codes:
                tech_logger.info(f"[CAIXA-PRETA] Código {c} não está mais presente na ECU.")
            self.known_dtcs = current_dtcs

    def _trigger_dtc_event(self, code: str):
        """Captures Freeze Frame (if available) and triggers confirmed DTC event."""
        freeze_data = {}
        ok_ff, resp_ff = self.conn.send_raw_command("020200", timeout=2.0)
        if ok_ff and resp_ff and "NO DATA" not in resp_ff.upper():
            freeze_data["RAW"] = resp_ff.strip()

        event = self.manager.trigger_event(
            event_type="DTC",
            code=code,
            title=f"DTC Confirmado: {code}",
            description=f"Novo código de falha detectado pela ECU durante o trajeto.",
            freeze_frame=freeze_data
        )
        self.event_detected.emit(event)

    def _check_suspicious_anomalies(self, sample: SampleData):
        """Analyzes sensor changes for sudden non-linear variations without false positives."""
        now_mono = sample.monotonic_ts
        if now_mono - self.last_suspicious_mono < 45.0:  # 45s cooldown
            return

        rpm = sample.values.get("RPM")
        map_val = sample.values.get("MAP")
        tps = sample.values.get("TPS")

        if self.last_sample:
            prev_rpm = self.last_sample.values.get("RPM")
            # 1. Sudden RPM drop under throttle
            if rpm is not None and prev_rpm is not None and tps is not None:
                if tps > 20 and prev_rpm > 1600 and (prev_rpm - rpm) > 450:
                    self.last_suspicious_mono = now_mono
                    event = self.manager.trigger_event(
                        event_type="SUSPEITO",
                        code="QUEDA_RPM",
                        title="Variação Brusca de RPM sob Carga",
                        description=f"RPM caiu subitamente de {prev_rpm} para {rpm} com borboleta em {tps}%."
                    )
                    self.event_detected.emit(event)
                    return

            # 2. Abnormal high MAP at lower RPM
            if map_val is not None and rpm is not None and tps is not None:
                if map_val > 90 and rpm < 2400 and tps > 50:
                    self.last_suspicious_mono = now_mono
                    event = self.manager.trigger_event(
                        event_type="SUSPEITO",
                        code="MAP_ELEVADO",
                        title="MAP Elevado sob Carga em Baixa Rotação",
                        description=f"Pressão absoluta no coletor atingiu {map_val} kPa a {rpm} rpm com TPS {tps}%."
                    )
                    self.event_detected.emit(event)
                    return

    def _on_consecutive_timeouts(self):
        """Handles repeated timeouts."""
        self.engine_state = "ECU_OFF"
        tech_logger.warn("[CAIXA-PRETA] Múltiplos timeouts consecutivos com a ECU.")

    def _handle_disconnection(self):
        """Auto-reconnection loop with backoff."""
        tech_logger.warn("[CAIXA-PRETA] Conexão serial perdida. Tentando reconectar...")
        self.manager.trigger_event(
            event_type="COMUNICACAO",
            code="ELM_DESCONECTADO",
            title="Perda de Comunicação com ELM327",
            description="O adaptador serial foi desconectado ou não respondeu."
        )

        backoffs = [2.0, 3.0, 5.0, 8.0]
        idx = 0
        while self._running and not self.conn.is_connected:
            delay = backoffs[min(idx, len(backoffs) - 1)]
            time.sleep(delay)
            idx += 1

            tech_logger.info(f"[CAIXA-PRETA] Tentativa de reconexão #{idx}...")
            ok, _ = self.conn.connect()
            if ok:
                ok_init, _ = self.conn.initialize_elm()
                if ok_init:
                    self.conn.test_ecu_communication()
                    tech_logger.success("[CAIXA-PRETA] ELM327 reconectado com sucesso!")
                    event = self.manager.trigger_event(
                        event_type="COMUNICACAO",
                        code="ELM_RECONECTADO",
                        title="Comunicação Restabelecida",
                        description="Conexão com o adaptador ELM327 e ECU foi restaurada."
                    )
                    self.event_detected.emit(event)
                    break
