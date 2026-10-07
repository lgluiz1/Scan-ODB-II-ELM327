"""Mock ELM327 adapter for offline simulation and automated verification.
Simulates a Renault Logan 2018 1.0 ECU with dynamic trip telemetry,
including climbing a hill, low RPM, high MAP, misfire P0300 onset, and recovery.
"""
import time
import math
from typing import Tuple, List, Dict, Any
from elm327.connection import SerialPortInfo
from utils.logger import tech_logger


class MockELM327Connection:
    """Simulates an ELM327 v1.5 connected to a Renault Logan 2018 1.0 ECU."""

    def __init__(self, port: str = "SIMULAÇÃO_MOCK", baudrate: int = 38400, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_connected = False
        self.elm_version = "ELM327 v1.5 (Simulado)"
        self.protocol_name = "ISO 15765-4 CAN (11 bit ID, 500 kbaud)"
        self.protocol_id = "6"
        self.battery_voltage = "12.6V"
        self.ecu_connected = False
        self.inter_command_delay = 0.02

        # Telemetry cycle counter for trip scenario simulation
        self.cycle_count = 0
        self.scenario_mode = "STATIC_DTC"  # "STATIC_DTC" or "TRIP_SIMULATION"

        # Static DTC fallback (if queried directly outside trip)
        self.simulated_stored_dtcs = ["P0106", "P0300"]
        self.simulated_pending_dtcs = ["P0130"]
        self.simulated_permanent_dtcs = ["P0420"]

    @staticmethod
    def list_available_ports() -> List[SerialPortInfo]:
        return [SerialPortInfo("SIMULAÇÃO (MOCK)", "Ambiente Virtual de Teste", "MOCK-001")]

    def connect(self) -> Tuple[bool, str]:
        tech_logger.info("[MOCK] Conectando ao ambiente virtual simulado...")
        time.sleep(0.05)
        self.is_connected = True
        tech_logger.success("[MOCK] Conectado ao adaptador simulado.")
        return True, "Conectado ao simulador."

    def disconnect(self):
        self.is_connected = False
        self.ecu_connected = False
        tech_logger.info("[MOCK] Conexão simulada desconectada.")

    def reset_scenario(self):
        self.cycle_count = 0

    def send_raw_command(self, cmd: str, timeout: float = None) -> Tuple[bool, str]:
        if not self.is_connected:
            return False, "Adaptador simulado desconectado."

        clean = cmd.strip().upper()
        tech_logger.tx(clean)
        time.sleep(0.01)

        response = ""
        # AT Commands
        if clean == "ATZ" or clean == "ATI":
            response = "ELM327 v1.5"
        elif clean in ["ATE0", "ATL0", "ATS0", "ATH0", "ATSP0", "ATAL"]:
            response = "OK"
        elif clean == "ATRV":
            response = self.battery_voltage
        elif clean == "ATDP":
            response = "ISO 15765-4 (CAN 11/500)"
        elif clean == "ATDPN":
            response = "6"

        # Mode 01 Supported PIDs
        elif clean == "0100":
            # PIDs 01-20: 0104, 0105, 0106, 0107, 010B, 010C, 010D, 010E, 010F, 0110, 0111, 0114, 0115, 011F
            response = "41 00 BE 3F B8 10"
        elif clean == "0120":
            # PIDs 21-40: 0124 Lambda
            response = "41 20 80 00 00 00"

        # Mode 01 Telemetry PIDs with Logan Trip Scenario Progression
        elif clean == "010C":  # RPM
            self.cycle_count += 1
            if self.cycle_count < 10:
                # Normal cruise (approx 2100 rpm)
                rpm = 2100 + (self.cycle_count % 3) * 30
            elif self.cycle_count < 18:
                # Climbing hill: RPM drops under load (approx 1450 rpm)
                rpm = 1480 - (self.cycle_count - 10) * 40
            elif self.cycle_count < 24:
                # Misfire onset! Sudden drop to 950 rpm
                rpm = 940 + (self.cycle_count % 2) * 50
            else:
                # Recovery (approx 1900 rpm)
                rpm = 1920
            # ((A * 256) + B) / 4 = rpm -> value * 4 = raw
            raw = rpm * 4
            a = (raw >> 8) & 0xFF
            b = raw & 0xFF
            response = f"41 0C {a:02X} {b:02X}"

        elif clean == "010B":  # MAP (kPa)
            if self.cycle_count < 10:
                map_kpa = 38
            elif self.cycle_count < 18:
                # High MAP under load / hill climb: 89 kPa
                map_kpa = 89
            elif self.cycle_count < 24:
                map_kpa = 94
            else:
                map_kpa = 42
            response = f"41 0B {map_kpa:02X}"

        elif clean == "010D":  # SPEED (km/h)
            if self.cycle_count < 10:
                speed = 60
            elif self.cycle_count < 18:
                speed = 45
            elif self.cycle_count < 24:
                speed = 30
            else:
                speed = 50
            response = f"41 0D {speed:02X}"

        elif clean == "0111":  # TPS (%)
            # A * 100 / 255 -> A = pct * 255 / 100
            if self.cycle_count < 10:
                tps = 22
            elif self.cycle_count < 24:
                tps = 68  # Throttle pressed trying to climb
            else:
                tps = 28
            raw_tps = int(tps * 255 / 100)
            response = f"41 11 {raw_tps:02X}"

        elif clean == "0104":  # LOAD (%)
            load = 84 if 10 <= self.cycle_count < 24 else 35
            raw_load = int(load * 255 / 100)
            response = f"41 04 {raw_load:02X}"

        elif clean == "0105":  # ECT (°C)
            # A - 40 = 88°C -> A = 128 (0x80)
            response = "41 05 80"

        elif clean == "0106":  # STFT (%)
            # (A - 128) * 100 / 128
            # In hill climb, fuel trim rises to +12%
            stft = 12.0 if 10 <= self.cycle_count < 24 else 1.5
            a = int((stft * 128 / 100) + 128)
            response = f"41 06 {a:02X}"

        elif clean == "0107":  # LTFT (%)
            response = "41 07 84"  # ~3.1%

        elif clean == "0114":  # O2 S1 (Pré-Cat: Oscillating rapidly between 0.1V and 0.88V)
            v1 = 0.48 + 0.38 * math.sin(time.time() * 3.5)
            raw_a1 = max(0, min(255, int(v1 * 200)))
            response = f"41 14 {raw_a1:02X} 80"

        elif clean == "0115":  # O2 S2 (Pós-Cat: Stable around 0.58V with slight drift)
            v2 = 0.58 + 0.05 * math.sin(time.time() * 0.4)
            raw_a2 = max(0, min(255, int(v2 * 200)))
            response = f"41 15 {raw_a2:02X} 80"

        elif clean == "0124":  # Lambda equivalence ratio
            ratio = 1.000 + 0.015 * math.sin(time.time() * 3.5)
            raw_ab = max(0, min(65535, int(ratio * 32768)))
            a = (raw_ab >> 8) & 0xFF
            b = raw_ab & 0xFF
            response = f"41 24 {a:02X} {b:02X} 80 00"

        elif clean == "010E":  # TIMING
            response = "41 0E 88"  # ~4°

        elif clean == "0110":  # MAF
            response = "41 10 03 E8"  # 10.00 g/s

        # Mode 04 - Clear Diagnostic Trouble Codes
        elif clean == "04":
            self.cycle_count = 0
            self.cleared = True
            response = "44"

        # Mode 03 - DTCs
        elif clean == "03":
            if getattr(self, "cleared", False):
                response = "43 00 00 00 00 00 00"
            elif self.scenario_mode == "STATIC_DTC":
                response = "43 01 06 03 00 00 00"
            else:
                # In trip simulation, P0300 appears when cycle reaches misfire onset (>=16)
                if self.cycle_count >= 16:
                    response = "43 03 00 00 00 00 00"  # P0300
                else:
                    response = "43 00 00 00 00 00 00"  # No DTCs initially

        # Mode 07 - Pending DTCs
        elif clean == "07":
            if getattr(self, "cleared", False):
                response = "47 00 00 00 00 00 00"
            elif self.scenario_mode == "STATIC_DTC":
                response = "47 01 30 00 00 00 00"
            else:
                response = "47 00 00 00 00 00 00"

        # Mode 0A - Permanent DTCs
        elif clean == "0A":
            if getattr(self, "cleared", False):
                response = "4A 00 00 00 00 00 00"
            else:
                response = "4A 04 20 00 00 00 00"

        # Freeze Frame Mode 02
        elif clean.startswith("02"):
            response = "42 02 00 03 00"  # FF for P0300

        else:
            response = "NO DATA"

        tech_logger.rx(response)
        return True, response

    def initialize_elm(self) -> Tuple[bool, str]:
        tech_logger.info("[MOCK] Inicializando ELM327 simulado...")
        time.sleep(0.05)
        self.send_raw_command("ATZ")
        self.send_raw_command("ATE0")
        self.send_raw_command("ATL0")
        self.send_raw_command("ATS0")
        self.send_raw_command("ATH0")
        self.send_raw_command("ATSP0")
        self.send_raw_command("ATRV")
        tech_logger.success("[MOCK] ELM327 simulado pronto.")
        return True, "ELM327 simulado inicializado."

    def test_ecu_communication(self) -> Tuple[bool, str]:
        tech_logger.info("[MOCK] Testando comunicação com ECU simulada (0100)...")
        time.sleep(0.05)
        self.send_raw_command("0100")
        self.ecu_connected = True
        tech_logger.success("[MOCK] ECU do Logan simulada respondeu positivamente!")
        return True, f"ECU conectada! Protocolo: {self.protocol_name}"
