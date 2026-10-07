"""DTC Reader implementation for querying OBD modes 03, 07, and 0A.
"""
from typing import List, Tuple
from dataclasses import dataclass
from obd.parser import parse_dtc_response
from dtc.database import get_dtc_info, DTCMeta
from utils.logger import tech_logger


@dataclass
class DTCItem:
    code: str
    status: str      # 'Confirmado', 'Pendente', 'Permanente'
    mode: str        # '03', '07', '0A'
    meta: DTCMeta


class DTCReader:
    """Handles querying and parsing of Diagnostic Trouble Codes via ELM327 connection."""

    def __init__(self, connection):
        self.conn = connection

    def read_all_dtcs(self) -> Tuple[List[DTCItem], str]:
        """
        Query Mode 03 (Stored), Mode 07 (Pending), and Mode 0A (Permanent).
        Returns combined list of DTCItem and status message.
        """
        if not self.conn.is_connected:
            return [], "Adaptador ELM327 não está conectado."

        all_items: List[DTCItem] = []
        seen = set()

        # 1. Mode 03: Stored DTCs
        tech_logger.info("Consultando códigos confirmados (Mode 03)...")
        ok_03, resp_03 = self.conn.send_raw_command("03")
        if ok_03:
            stored_codes = parse_dtc_response(resp_03, "43")
            for c in stored_codes:
                all_items.append(DTCItem(
                    code=c,
                    status="Confirmado",
                    mode="03",
                    meta=get_dtc_info(c)
                ))
                seen.add(c)
            tech_logger.info(f"Mode 03 retornou {len(stored_codes)} código(s): {', '.join(stored_codes) if stored_codes else 'Nenhum'}")

        # 2. Mode 07: Pending DTCs
        tech_logger.info("Consultando códigos pendentes (Mode 07)...")
        ok_07, resp_07 = self.conn.send_raw_command("07")
        if ok_07:
            pending_codes = parse_dtc_response(resp_07, "47")
            for c in pending_codes:
                if c in seen:
                    # Update status to Confirmed & Pending
                    for it in all_items:
                        if it.code == c:
                            it.status = "Confirmado & Pendente"
                else:
                    all_items.append(DTCItem(
                        code=c,
                        status="Pendente",
                        mode="07",
                        meta=get_dtc_info(c)
                    ))
                    seen.add(c)
            tech_logger.info(f"Mode 07 retornou {len(pending_codes)} código(s): {', '.join(pending_codes) if pending_codes else 'Nenhum'}")

        # 3. Mode 0A: Permanent DTCs (if supported)
        tech_logger.info("Consultando códigos permanentes (Mode 0A)...")
        ok_0a, resp_0a = self.conn.send_raw_command("0A")
        if ok_0a:
            perm_codes = parse_dtc_response(resp_0a, "4A")
            for c in perm_codes:
                if c in seen:
                    for it in all_items:
                        if it.code == c:
                            it.status += " / Permanente"
                else:
                    all_items.append(DTCItem(
                        code=c,
                        status="Permanente",
                        mode="0A",
                        meta=get_dtc_info(c)
                    ))
            tech_logger.info(f"Mode 0A retornou {len(perm_codes)} código(s): {', '.join(perm_codes) if perm_codes else 'Nenhum'}")

        msg = f"Leitura concluída. Total de {len(all_items)} código(s) encontrado(s)."
        tech_logger.success(msg)
        return all_items, msg

    def clear_all_dtcs(self) -> Tuple[bool, str]:
        """
        Sends OBD2 Mode 04 ('04') to reset diagnostic trouble codes,
        freeze frame data, oxygen sensor test results, and monitor status.
        """
        if not self.conn or not self.conn.is_connected:
            return False, "Adaptador ELM327 não está conectado."

        tech_logger.warn("Enviando comando OBD2 Mode 04 para apagar todos os códigos da ECU...")
        ok, resp = self.conn.send_raw_command("04", timeout=5.0)

        if not ok:
            msg = f"Falha ao enviar comando de limpeza (Mode 04): {resp}"
            tech_logger.error(msg)
            return False, msg

        clean = resp.upper().strip()
        # Acceptable responses: "44", "OK", "44 00", or responses without "ERROR" / "NO DATA"
        if "44" in clean or "OK" in clean:
            msg = "Comando de limpeza (Mode 04) aceito com sucesso pela ECU."
            tech_logger.success(msg)
            return True, msg
        elif "NO DATA" in clean or "UNABLE" in clean or "BUS ERROR" in clean:
            msg = f"A ECU não confirmou a limpeza: {resp}"
            tech_logger.error(msg)
            return False, msg
        else:
            msg = f"Comando Mode 04 executado. Resposta recebida: {resp}"
            tech_logger.info(msg)
            return True, msg
