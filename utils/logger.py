"""Technical logger with timestamping and GUI notification signal/callbacks.
"""
import datetime
from typing import Callable, List


class LogEntry:
    def __init__(self, level: str, message: str, raw: str = ""):
        self.timestamp = datetime.datetime.now()
        self.level = level  # 'INFO', 'TX', 'RX', 'WARN', 'ERROR', 'SUCCESS'
        self.message = message
        self.raw = raw

    def formatted(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{time_str}]"
        if self.level == "TX":
            return f"{prefix} >>> TX: {self.message}"
        elif self.level == "RX":
            return f"{prefix} <<< RX: {self.message}"
        elif self.level == "ERROR":
            return f"{prefix} [ERRO] {self.message}"
        elif self.level == "WARN":
            return f"{prefix} [AVISO] {self.message}"
        elif self.level == "SUCCESS":
            return f"{prefix} [OK] {self.message}"
        else:
            return f"{prefix} {self.message}"


class TechnicalLogger:
    def __init__(self):
        self.entries: List[LogEntry] = []
        self._listeners: List[Callable[[LogEntry], None]] = []

    def add_listener(self, callback: Callable[[LogEntry], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[LogEntry], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _log(self, level: str, message: str, raw: str = ""):
        entry = LogEntry(level, message, raw)
        self.entries.append(entry)
        for listener in list(self._listeners):
            try:
                listener(entry)
            except Exception:
                pass

    def info(self, msg: str):
        self._log("INFO", msg)

    def tx(self, cmd: str):
        self._log("TX", cmd)

    def rx(self, resp: str):
        self._log("RX", resp)

    def warn(self, msg: str):
        self._log("WARN", msg)

    def error(self, msg: str):
        self._log("ERROR", msg)

    def success(self, msg: str):
        self._log("SUCCESS", msg)

    def clear(self):
        self.entries.clear()

    def get_full_log(self) -> str:
        return "\n".join(e.formatted() for e in self.entries)


# Global singleton instance
tech_logger = TechnicalLogger()
