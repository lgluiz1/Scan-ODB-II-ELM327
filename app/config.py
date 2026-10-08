"""Application configuration and default settings.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ConnectionConfig:
    port: str = ""
    baudrate: int = 38400
    timeout: float = 2.0
    retry_count: int = 2
    inter_command_delay: float = 0.06  # 60ms between commands


SUPPORTED_BAUDRATES: List[int] = [
    9600,
    19200,
    38400,   # Standard default for most ELM327 USB (CH340 / FTDI / PL2303)
    57600,
    115200,
    230400,
    500000
]

APP_NAME = "ODBScan II"
APP_VERSION = "1.3.0"
VEHICLE_PROFILE_DEFAULT = "Universal OBD2 / CAN Bus (SAE J1979)"
SAFETY_WARNING = "AVISO DE SEGURANÇA: Esta ferramenta opera em modo SOMENTE LEITURA. Não apague os códigos antes de salvar o diagnóstico completo."

GITHUB_REPO = "lgluiz1/Scan-ODB-II-ELM327"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

