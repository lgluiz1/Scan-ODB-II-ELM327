"""Serial connection manager and ELM327 protocol handler.
"""
import time
from typing import List, Optional, Tuple, Dict, Any
import serial
import serial.tools.list_ports

from elm327.commands import (
    CMD_RESET, CMD_ECHO_OFF, CMD_LINEFEEDS_OFF, CMD_SPACES_OFF,
    CMD_HEADERS_OFF, CMD_SET_PROTOCOL_AUTO, CMD_DISPLAY_PROTOCOL,
    CMD_DISPLAY_PROTOCOL_NUM, CMD_READ_VOLTAGE, CMD_DESCRIBE_CHIP,
    PROTOCOL_MAP, ELM_PROMPT, RESP_NO_DATA, RESP_UNABLE_TO_CONNECT,
    RESP_BUS_BUSY, RESP_BUS_ERROR
)
from utils.logger import tech_logger


class SerialPortInfo:
    def __init__(self, port: str, description: str, hwid: str):
        self.port = port
        self.description = description
        self.hwid = hwid

    def display_name(self) -> str:
        if self.description and self.description != "n/a" and self.description != self.port:
            return f"{self.port} ({self.description})"
        return self.port


class ELM327Connection:
    """Handles low-level serial communication and initialization of ELM327."""

    def __init__(self, port: str = "", baudrate: int = 38400, timeout: float = 2.5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.is_connected = False
        self.elm_version = "Desconhecido"
        self.protocol_name = "Desconhecido"
        self.protocol_id = ""
        self.battery_voltage = "0.0V"
        self.ecu_connected = False
        self.inter_command_delay = 0.05

    @staticmethod
    def list_available_ports() -> List[SerialPortInfo]:
        """Detect and return all serial COM ports available on the system."""
        ports = serial.tools.list_ports.comports()
        result = []
        for p in ports:
            result.append(SerialPortInfo(p.device, p.description, p.hwid))
        return result

    def connect(self) -> Tuple[bool, str]:
        """Open the serial port and verify basic communication with the ELM327 adapter."""
        if not self.port:
            return False, "Nenhuma porta COM selecionada."

        tech_logger.info(f"Abrindo porta {self.port} a {self.baudrate} bps (timeout={self.timeout}s)...")
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Give device a short moment to settle
            time.sleep(0.2)
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            self.is_connected = True
            tech_logger.success(f"Porta {self.port} aberta com sucesso.")
            return True, f"Porta {self.port} aberta."
        except serial.SerialException as ex:
            self.is_connected = False
            self.serial = None
            msg = f"Falha ao abrir porta {self.port}: {str(ex)}"
            tech_logger.error(msg)
            return False, msg
        except Exception as ex:
            self.is_connected = False
            self.serial = None
            msg = f"Erro inesperado ao acessar {self.port}: {str(ex)}"
            tech_logger.error(msg)
            return False, msg

    def disconnect(self):
        """Close the serial port."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except Exception:
                pass
        self.serial = None
        self.is_connected = False
        self.ecu_connected = False
        self.elm_version = "Desconhecido"
        self.protocol_name = "Desconhecido"
        tech_logger.info("Conexão serial fechada.")

    def send_raw_command(self, cmd: str, timeout: Optional[float] = None) -> Tuple[bool, str]:
        """Send a raw command to ELM327 and read response until prompt '>'."""
        if not self.serial or not self.serial.is_open:
            return False, "Porta serial não está aberta."

        clean_cmd = cmd.strip()
        tech_logger.tx(clean_cmd)

        try:
            # Clear input buffer
            self.serial.reset_input_buffer()

            # Send command terminated with CR
            payload = (clean_cmd + "\r").encode("ascii", errors="replace")
            self.serial.write(payload)
            self.serial.flush()

            # Read until '>' or timeout
            t_timeout = timeout if timeout is not None else self.timeout
            start_time = time.time()
            buffer = bytearray()

            while time.time() - start_time < t_timeout:
                if self.serial.in_waiting > 0:
                    b = self.serial.read(self.serial.in_waiting)
                    buffer.extend(b)
                    if b">" in buffer:
                        break
                else:
                    time.sleep(0.02)

            raw_str = buffer.decode("ascii", errors="replace").replace("\r", "\n")
            lines = [line.strip() for line in raw_str.split("\n") if line.strip()]

            # Filter out echo and prompt
            cleaned_lines = []
            for l in lines:
                if l == clean_cmd:
                    continue  # Echo
                if l == ">":
                    continue
                if l.endswith(">"):
                    l = l[:-1].strip()
                if l:
                    cleaned_lines.append(l)

            response = "\n".join(cleaned_lines)
            tech_logger.rx(response if response else "[Sem resposta]")

            if self.inter_command_delay > 0:
                time.sleep(self.inter_command_delay)

            return True, response
        except serial.SerialTimeoutException:
            msg = "Timeout na escrita serial."
            tech_logger.error(msg)
            return False, msg
        except Exception as ex:
            msg = f"Erro de comunicação: {str(ex)}"
            tech_logger.error(msg)
            return False, msg

    def initialize_elm(self) -> Tuple[bool, str]:
        """Initialize ELM327 with standard AT command sequence."""
        if not self.is_connected:
            return False, "Adaptador não está conectado."

        tech_logger.info("Iniciando sequência de inicialização do ELM327...")

        # 1. ATZ (Reset) - wait extra time for ELM banner
        ok, resp = self.send_raw_command(CMD_RESET, timeout=2.0)
        time.sleep(0.8)
        if not ok or not resp:
            # Second attempt with ATI
            ok, resp = self.send_raw_command(CMD_DESCRIBE_CHIP, timeout=1.5)

        if resp:
            self.elm_version = resp.split("\n")[0].strip()
            tech_logger.success(f"ELM327 identificou-se como: {self.elm_version}")
        else:
            self.elm_version = "ELM327 (Sem identificação clara)"
            tech_logger.warn("ELM327 não retornou banner de versão claro, continuando inicialização...")

        # 2. Desligar Echo (ATE0)
        self.send_raw_command(CMD_ECHO_OFF)

        # 3. Desligar Linefeeds (ATL0)
        self.send_raw_command(CMD_LINEFEEDS_OFF)

        # 4. Desligar Espaços (ATS0)
        self.send_raw_command(CMD_SPACES_OFF)

        # 5. Desligar Headers extras (ATH0)
        self.send_raw_command(CMD_HEADERS_OFF)

        # 6. Definir protocolo automático (ATSP0)
        self.send_raw_command(CMD_SET_PROTOCOL_AUTO)

        # 7. Ler tensão da bateria (ATRV)
        ok_v, resp_v = self.send_raw_command(CMD_READ_VOLTAGE, timeout=1.5)
        if ok_v and resp_v and "V" in resp_v.upper():
            self.battery_voltage = resp_v.strip()
            tech_logger.info(f"Tensão da bateria medida pelo adaptador: {self.battery_voltage}")

        tech_logger.success("Inicialização do adaptador ELM327 concluída.")
        return True, "ELM327 inicializado com sucesso."

    def test_ecu_communication(self) -> Tuple[bool, str]:
        """
        Send Mode 01 PID 00 (Supported PIDs) to verify ECU communication
        and identify active OBD protocol.
        """
        if not self.is_connected:
            return False, "Adaptador não conectado."

        tech_logger.info("Testando comunicação com a ECU (Enviando '0100')...")
        # Allow up to 5s for ECU protocol search (ELM327 searches protocols on first OBD command)
        ok, resp = self.send_raw_command("0100", timeout=6.0)

        if not ok:
            self.ecu_connected = False
            return False, "Falha no envio de comando para a ECU."

        upper_resp = resp.upper()

        if RESP_UNABLE_TO_CONNECT in upper_resp or RESP_BUS_BUSY in upper_resp or RESP_BUS_ERROR in upper_resp:
            self.ecu_connected = False
            msg = "Não foi possível conectar à ECU. Verifique se a chave de ignição está na posição LIGADA (ON)."
            tech_logger.error(msg)
            return False, msg

        if RESP_NO_DATA in upper_resp:
            self.ecu_connected = False
            msg = "ECU retornou 'NO DATA'. Verifique se a ignição está ligada."
            tech_logger.warn(msg)
            return False, msg

        # Check for positive response (Mode 01 response starts with 41)
        # Clean spaces just in case
        clean = upper_resp.replace(" ", "")
        if "4100" in clean:
            self.ecu_connected = True
            tech_logger.success("Comunicação com a ECU estabelecida com sucesso!")

            # Check protocol
            self._query_active_protocol()
            return True, f"ECU conectada! Protocolo: {self.protocol_name}"

        # If it returned some other hex response
        if any(c in upper_resp for c in ["41", "OK"]):
            self.ecu_connected = True
            self._query_active_protocol()
            return True, f"ECU conectada! Protocolo: {self.protocol_name}"

        self.ecu_connected = False
        msg = f"Resposta inesperada da ECU: '{resp}'. Verifique se a ignição está ligada."
        tech_logger.warn(msg)
        return False, msg

    def _query_active_protocol(self):
        """Query active protocol from ELM327 using ATDP and ATDPN."""
        ok_dp, resp_dp = self.send_raw_command(CMD_DISPLAY_PROTOCOL)
        if ok_dp and resp_dp and resp_dp != "?":
            self.protocol_name = resp_dp.strip()

        ok_dpn, resp_dpn = self.send_raw_command(CMD_DISPLAY_PROTOCOL_NUM)
        if ok_dpn and resp_dpn:
            num = resp_dpn.replace("A", "").strip()
            if num in PROTOCOL_MAP:
                self.protocol_id = num
                if self.protocol_name == "Desconhecido" or "AUTO" in self.protocol_name:
                    self.protocol_name = PROTOCOL_MAP[num]

        tech_logger.info(f"Protocolo ativo detectado: {self.protocol_name}")
