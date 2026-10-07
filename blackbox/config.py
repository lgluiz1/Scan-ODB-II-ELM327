"""Configuration and thresholds for the Blackbox (Modo Viagem) continuous monitor.
"""
import os
from dataclasses import dataclass


BASE_STORAGE_DIR = os.path.abspath(os.path.join(".", "DiagnosticosOBD", "Viagens"))

# Default time buffer parameters in seconds
DEFAULT_PRE_EVENT_SECONDS = 60    # 60s of data before an event
DEFAULT_POST_EVENT_SECONDS = 30   # 30s of data after an event

# Acquisition timing
ADAPTIVE_MIN_CYCLE_MS = 250       # Fast cycle floor (250ms)
ADAPTIVE_MAX_CYCLE_MS = 1000      # Slow cycle ceiling (1000ms)
DEFAULT_INTER_COMMAND_DELAY = 0.04 # 40ms safety between OBD commands

# Event cooldown in seconds (prevents repeating events for identical active DTC)
DTC_EVENT_COOLDOWN_SECONDS = 90.0
SUSPICIOUS_EVENT_COOLDOWN_SECONDS = 60.0

# Anomaly thresholds (configured conservatively to prevent false positives)
ANOMALY_MAP_SPIKE_KPA = 88         # MAP above this under low RPM / load suggests high manifold pressure
ANOMALY_RPM_DROP_DELTA = 400       # Sudden RPM drop (>400 rpm in one cycle) under load
ANOMALY_CONSECUTIVE_TIMEOUTS = 3   # Trigger communication event after 3 consecutive timeouts


@dataclass
class BlackboxConfig:
    pre_event_seconds: int = DEFAULT_PRE_EVENT_SECONDS
    post_event_seconds: int = DEFAULT_POST_EVENT_SECONDS
    adaptive_min_ms: int = ADAPTIVE_MIN_CYCLE_MS
    adaptive_max_ms: int = ADAPTIVE_MAX_CYCLE_MS
    storage_dir: str = BASE_STORAGE_DIR
    auto_start_on_connect: bool = False
    detect_suspicious_events: bool = True
    auto_reconnect: bool = True
    save_continuous_csv: bool = True
    generate_html_reports: bool = True
    anomaly_consecutive_timeouts: int = ANOMALY_CONSECUTIVE_TIMEOUTS
