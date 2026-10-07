"""Crash recovery utility for unfinalized trips.
"""
import os
import json
from typing import List, Dict, Any, Optional
from blackbox.config import BASE_STORAGE_DIR


class CrashRecovery:
    """Detects and recovers trips that were left unfinalized due to unexpected shutdown."""

    @staticmethod
    def find_incomplete_trips(storage_dir: str = BASE_STORAGE_DIR) -> List[Dict[str, Any]]:
        incomplete = []
        if not os.path.exists(storage_dir):
            return incomplete

        for entry in os.scandir(storage_dir):
            if entry.is_dir():
                json_path = os.path.join(entry.path, "viagem.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if data.get("status") == "EM_ANDAMENTO":
                                incomplete.append(data)
                    except Exception:
                        pass
        return incomplete

    @staticmethod
    def recover_trip(folder_path: str) -> bool:
        json_path = os.path.join(folder_path, "viagem.json")
        if not os.path.exists(json_path):
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["status"] = "RECUPERADA"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
