"""OBD2 PID definitions, bitmask discovery, and engineering unit decoders.
Strictly follows SAE J1979 specifications for Mode 01.
"""
from typing import Dict, Any, Optional, Callable, Set, List
from dataclasses import dataclass
from obd.parser import clean_hex_stream


@dataclass
class PIDDefinition:
    pid: str            # e.g. "010C"
    name: str           # e.g. "RPM"
    description: str    # e.g. "Rotação do Motor"
    unit: str           # e.g. "rpm"
    bytes_returned: int # e.g. 2
    decoder: Callable[[List[int]], Any]


# Decoders according to SAE J1979
def decode_load(b: List[int]) -> float:
    # A * 100 / 255
    return round((b[0] * 100.0) / 255.0, 1)

def decode_temp(b: List[int]) -> int:
    # A - 40
    return b[0] - 40

def decode_fuel_trim(b: List[int]) -> float:
    # (A - 128) * 100 / 128
    return round(((b[0] - 128) * 100.0) / 128.0, 1)

def decode_fuel_pressure(b: List[int]) -> int:
    # A * 3
    return b[0] * 3

def decode_map(b: List[int]) -> int:
    # A (kPa)
    return b[0]

def decode_rpm(b: List[int]) -> int:
    # ((A * 256) + B) / 4
    return int(((b[0] * 256) + b[1]) / 4)

def decode_speed(b: List[int]) -> int:
    # A (km/h)
    return b[0]

def decode_timing_advance(b: List[int]) -> float:
    # (A / 2) - 64
    return round((b[0] / 2.0) - 64.0, 1)

def decode_maf(b: List[int]) -> float:
    # ((A * 256) + B) / 100
    return round(((b[0] * 256) + b[1]) / 100.0, 2)

def decode_tps(b: List[int]) -> float:
    # A * 100 / 255
    return round((b[0] * 100.0) / 255.0, 1)

def decode_o2_voltage(b: List[int]) -> float:
    # A / 200 (Volts)
    return round(b[0] / 200.0, 3)

def decode_run_time(b: List[int]) -> int:
    # (A * 256) + B (seconds)
    return (b[0] * 256) + b[1]

def decode_lambda(b: List[int]) -> float:
    # ((A * 256) + B) / 32768
    ratio = ((b[0] * 256) + b[1]) / 32768.0
    return round(ratio, 3)


PID_CATALOG: Dict[str, PIDDefinition] = {
    "0104": PIDDefinition("0104", "LOAD", "Carga Calculada", "%", 1, decode_load),
    "0105": PIDDefinition("0105", "ECT", "Temperatura do Motor", "°C", 1, decode_temp),
    "0106": PIDDefinition("0106", "STFT", "Ajuste de Combustível Curto Prazo", "%", 1, decode_fuel_trim),
    "0107": PIDDefinition("0107", "LTFT", "Ajuste de Combustível Longo Prazo", "%", 1, decode_fuel_trim),
    "010A": PIDDefinition("010A", "FRP", "Pressão de Combustível", "kPa", 1, decode_fuel_pressure),
    "010B": PIDDefinition("010B", "MAP", "Pressão Absoluta do Coletor", "kPa", 1, decode_map),
    "010C": PIDDefinition("010C", "RPM", "Rotação do Motor", "rpm", 2, decode_rpm),
    "010D": PIDDefinition("010D", "SPEED", "Velocidade do Veículo", "km/h", 1, decode_speed),
    "010E": PIDDefinition("010E", "TIMING", "Avanço de Ignição", "°", 1, decode_timing_advance),
    "010F": PIDDefinition("010F", "IAT", "Temp. Ar de Admissão", "°C", 1, decode_temp),
    "0110": PIDDefinition("0110", "MAF", "Fluxo de Massa de Ar", "g/s", 2, decode_maf),
    "0111": PIDDefinition("0111", "TPS", "Posição da Borboleta", "%", 1, decode_tps),
    "0114": PIDDefinition("0114", "O2_B1S1", "Sonda Lambda Pré-Cat (B1S1)", "V", 2, decode_o2_voltage),
    "0115": PIDDefinition("0115", "O2_B1S2", "Sonda Lambda Pós-Cat (B1S2)", "V", 2, decode_o2_voltage),
    "011F": PIDDefinition("011F", "RUNTIME", "Tempo de Funcionamento", "s", 2, decode_run_time),
    "0124": PIDDefinition("0124", "LAMBDA", "Equivalência Lambda", "λ", 4, decode_lambda),
}


def parse_pid_support_bitmap(raw_response: str, base_pid: int = 0) -> Set[str]:
    """
    Parses Mode 01 PID support response (e.g., 0100 -> 41 00 BE 3F B8 10).
    Returns a set of supported PID hex strings like {'0104', '0105', '010C', ...}
    """
    tokens = clean_hex_stream(raw_response)
    supported: Set[str] = set()

    # Look for response prefix 41 followed by PID base (00, 20, 40...)
    base_hex = f"{base_pid:02X}"
    start_idx = -1
    for i in range(len(tokens) - 1):
        if tokens[i] == "41" and tokens[i+1] == base_hex:
            start_idx = i + 2
            break

    if start_idx == -1 or len(tokens) < start_idx + 4:
        return supported

    try:
        bytes_data = [int(t, 16) for t in tokens[start_idx:start_idx+4]]
        # 32 bits representation
        bitmask = (bytes_data[0] << 24) | (bytes_data[1] << 16) | (bytes_data[2] << 8) | bytes_data[3]

        for i in range(1, 33):
            is_supported = (bitmask >> (32 - i)) & 1
            if is_supported:
                pid_num = base_pid + i
                pid_hex = f"01{pid_num:02X}"
                supported.add(pid_hex)
    except Exception:
        pass

    return supported


def decode_pid_value(pid_hex: str, raw_response: str) -> Optional[Any]:
    """
    Decodes the value of a specific PID from raw ELM327 response string.
    Expected response starts with 41 + PID (e.g. 41 0C 0F A0 for 010C).
    """
    if "NO DATA" in raw_response.upper() or "UNABLE" in raw_response.upper():
        return None

    clean_pid = pid_hex.upper().strip()
    if clean_pid not in PID_CATALOG:
        return None

    definition = PID_CATALOG[clean_pid]
    pid_byte_str = clean_pid[2:4]  # e.g. "0C"

    tokens = clean_hex_stream(raw_response)
    data_bytes: List[int] = []

    # Find position of 41 <PID>
    start_idx = -1
    for i in range(len(tokens) - 1):
        if tokens[i] == "41" and tokens[i+1] == pid_byte_str:
            start_idx = i + 2
            break

    if start_idx == -1:
        # Fallback for concatenated tokens e.g. "410C0FA0"
        for tok in tokens:
            if tok.startswith("41" + pid_byte_str) and len(tok) >= 4 + (definition.bytes_returned * 2):
                hex_payload = tok[4:4 + (definition.bytes_returned * 2)]
                data_bytes = [int(hex_payload[j:j+2], 16) for j in range(0, len(hex_payload), 2)]
                break
    else:
        # Take required number of bytes
        available = tokens[start_idx:start_idx + definition.bytes_returned]
        if len(available) >= definition.bytes_returned:
            try:
                data_bytes = [int(t, 16) for t in available]
            except ValueError:
                data_bytes = []

    if len(data_bytes) < definition.bytes_returned:
        return None

    try:
        return definition.decoder(data_bytes)
    except Exception:
        return None
