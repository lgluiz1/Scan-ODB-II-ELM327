"""OBD2 response parser for ELM327 hex strings and frames.
"""
import re
from typing import List, Tuple, Optional


def clean_hex_stream(raw_text: str) -> List[str]:
    """
    Extract hex tokens from raw ELM327 multiline output.
    Handles CAN multi-line frame prefixes (e.g., '0: 43 ...', '1: ...', '2: ...'),
    removes extra spaces, prompts, and headers.
    """
    lines = raw_text.strip().split("\n")
    tokens: List[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove prompt '>'
        line = line.replace(">", "").strip()
        # Remove CAN multi-frame index prefix like '0:', '1:', '2:' or '00:', '01:'
        line = re.sub(r"^[0-9A-Fa-f]{1,2}:\s*", "", line)
        # Split into tokens
        parts = line.split()
        for p in parts:
            p_clean = p.strip()
            # If token is valid hex byte or multiple bytes
            if re.fullmatch(r"[0-9A-Fa-f]+", p_clean):
                # If length is even, break down into 2-char hex bytes
                if len(p_clean) % 2 == 0:
                    for i in range(0, len(p_clean), 2):
                        tokens.append(p_clean[i:i+2].upper())
                else:
                    tokens.append(p_clean.upper())

    return tokens


def decode_single_dtc(b1: int, b2: int) -> Optional[str]:
    """
    Decode standard OBD2 2-byte DTC representation into string (e.g. 'P0106').
    Returns None if code is 0x0000 (padding/empty).
    """
    if b1 == 0 and b2 == 0:
        return None

    # First 2 bits indicate type:
    # 00: Powertrain (P)
    # 01: Chassis (C)
    # 10: Body (B)
    # 11: Network (U)
    category_bits = (b1 >> 6) & 0x03
    types = ["P", "C", "B", "U"]
    dtc_type = types[category_bits]

    # Next 2 bits indicate first digit: 0, 1, 2, 3
    dig1 = (b1 >> 4) & 0x03

    # Next 4 bits are 2nd digit in hex
    dig2 = b1 & 0x0F

    # Byte 2 contains digits 3 and 4
    dig3 = (b2 >> 4) & 0x0F
    dig4 = b2 & 0x0F

    return f"{dtc_type}{dig1:X}{dig2:X}{dig3:X}{dig4:X}"


def parse_dtc_response(raw_text: str, expected_mode_response: str) -> List[str]:
    """
    Parse DTCs from Mode 03 (expected '43'), Mode 07 (expected '47'), or Mode 0A (expected '4A').
    Returns a list of unique DTC strings.
    """
    upper_raw = raw_text.upper()
    if "NO DATA" in upper_raw or "UNABLE" in upper_raw or "BUS ERROR" in upper_raw:
        return []

    tokens = clean_hex_stream(raw_text)
    if not tokens:
        return []

    expected_prefix = expected_mode_response.upper()

    # Find where the response header starts
    # Some ECUs send message length byte after mode response (e.g., in CAN multi-frame: 43 04 01 06 ...)
    # or just raw bytes: 43 01 06 03 00 00 00
    start_idx = -1
    for i, t in enumerate(tokens):
        if t == expected_prefix:
            start_idx = i
            break

    if start_idx == -1:
        return []

    data_tokens = tokens[start_idx + 1:]
    if not data_tokens:
        return []

    # Check if first byte after mode is DTC count (common in CAN: e.g. 43 02 01 06 03 00 -> 02 means 2 DTCs)
    # If the first byte is non-zero and remainder len == count * 2, skip it
    dtc_bytes: List[int] = []
    try:
        raw_ints = [int(t, 16) for t in data_tokens]
    except ValueError:
        return []

    # If first byte is odd count indicator or header, inspect
    if len(raw_ints) % 2 != 0:
        # First byte might be number of DTCs or length
        # e.g., [0x02, 0x01, 0x06, 0x03, 0x00]
        raw_ints = raw_ints[1:]

    dtcs: List[str] = []
    for i in range(0, len(raw_ints) - 1, 2):
        b1 = raw_ints[i]
        b2 = raw_ints[i + 1]
        dtc = decode_single_dtc(b1, b2)
        if dtc and dtc not in dtcs:
            dtcs.append(dtc)

    return dtcs
