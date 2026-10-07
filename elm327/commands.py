"""ELM327 AT Commands and OBD Protocol Definitions.
"""
from typing import Dict

# Common ELM327 AT Commands
CMD_RESET = "ATZ"               # Reset all
CMD_ECHO_OFF = "ATE0"           # Echo off
CMD_ECHO_ON = "ATE1"            # Echo on
CMD_LINEFEEDS_OFF = "ATL0"      # Linefeeds off
CMD_SPACES_OFF = "ATS0"         # Spaces off
CMD_SPACES_ON = "ATS1"          # Spaces on
CMD_HEADERS_OFF = "ATH0"        # Headers off
CMD_HEADERS_ON = "ATH1"         # Headers on
CMD_SET_PROTOCOL_AUTO = "ATSP0" # Protocol Automatic
CMD_DISPLAY_PROTOCOL = "ATDP"   # Display protocol
CMD_DISPLAY_PROTOCOL_NUM = "ATDPN" # Display protocol number
CMD_READ_VOLTAGE = "ATRV"       # Read battery voltage
CMD_DESCRIBE_CHIP = "ATI"       # ELM327 device identification
CMD_ALLOW_LONG_MESSAGES = "ATAL"# Allow long (>7 bytes) messages

# Standard protocol map based on ATDP / ATDPN
PROTOCOL_MAP: Dict[str, str] = {
    "1": "SAE J1850 PWM (41.6 kbaud)",
    "2": "SAE J1850 VPW (10.4 kbaud)",
    "3": "ISO 9141-2 (5 baud init, 10.4 kbaud)",
    "4": "ISO 14230-4 KWP (5 baud init, 10.4 kbaud)",
    "5": "ISO 14230-4 KWP (fast init, 10.4 kbaud)",
    "6": "ISO 15765-4 CAN (11 bit ID, 500 kbaud)",
    "7": "ISO 15765-4 CAN (29 bit ID, 500 kbaud)",
    "8": "ISO 15765-4 CAN (11 bit ID, 250 kbaud)",
    "9": "ISO 15765-4 CAN (29 bit ID, 250 kbaud)",
    "A": "SAE J1939 CAN (29 bit ID, 250 kbaud)",
    "B": "USER1 CAN (11 bit ID, 125 kbaud)",
    "C": "USER2 CAN (11 bit ID, 50 kbaud)",
}

# Known ELM327 prompt character
ELM_PROMPT = ">"

# Error / special responses
RESP_NO_DATA = "NO DATA"
RESP_UNABLE_TO_CONNECT = "UNABLE TO CONNECT"
RESP_BUS_BUSY = "BUS BUSY"
RESP_BUS_ERROR = "BUS ERROR"
RESP_CAN_ERROR = "CAN ERROR"
RESP_SEARCHING = "SEARCHING..."
RESP_STOPPED = "STOPPED"
RESP_OK = "OK"
RESP_ERROR = "?"
