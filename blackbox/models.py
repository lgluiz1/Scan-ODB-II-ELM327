"""Data models for Blackbox trips, continuous samples, and diagnostic events.
"""
import time
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SampleData:
    timestamp: str                 # e.g. "2026-10-06 08:35:01.120"
    monotonic_ts: float            # time.monotonic()
    values: Dict[str, Any]         # e.g. {"RPM": 1420, "MAP": 45, "SPEED": 38, ...}

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "timestamp": self.timestamp,
            "monotonic_ts": round(self.monotonic_ts, 3),
        }
        d.update(self.values)
        return d


@dataclass
class TripEvent:
    event_id: str                  # e.g. "20261006_083521_P0300_001"
    event_type: str                # "DTC", "SUSPEITO", "COMUNICACAO"
    code: str                      # e.g. "P0300", "MAP_ANOMALIA", "ELM_DESCONECTADO"
    title: str
    description: str
    timestamp: str
    monotonic_ts: float
    trigger_sample: Optional[SampleData] = None
    freeze_frame: Dict[str, Any] = field(default_factory=dict)
    pre_samples: List[SampleData] = field(default_factory=list)
    post_samples: List[SampleData] = field(default_factory=list)
    folder_path: str = ""
    is_completed: bool = False     # True after post_event_seconds samples are captured

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
            "monotonic_ts": round(self.monotonic_ts, 3),
            "freeze_frame": self.freeze_frame,
            "pre_samples_count": len(self.pre_samples),
            "post_samples_count": len(self.post_samples),
            "folder_path": self.folder_path,
            "is_completed": self.is_completed
        }


@dataclass
class TripMetadata:
    trip_id: str
    folder_path: str
    start_time: str
    end_time: str = ""
    duration_sec: float = 0.0
    port: str = ""
    elm_version: str = ""
    protocol_name: str = ""
    vin: str = "N/A"
    supported_pids: List[str] = field(default_factory=list)
    events_count: int = 0
    dtc_count: int = 0
    disconnect_count: int = 0
    status: str = "EM_ANDAMENTO"   # "EM_ANDAMENTO", "FINALIZADA", "INTERROMPIDA", "RECUPERADA"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "folder_path": self.folder_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_sec": round(self.duration_sec, 1),
            "port": self.port,
            "elm_version": self.elm_version,
            "protocol_name": self.protocol_name,
            "vin": self.vin,
            "supported_pids": self.supported_pids,
            "events_count": self.events_count,
            "dtc_count": self.dtc_count,
            "disconnect_count": self.disconnect_count,
            "status": self.status
        }
