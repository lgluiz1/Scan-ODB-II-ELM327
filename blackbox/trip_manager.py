"""Trip manager for blackbox session lifecycles, file persistence, and circular buffers.
"""
import os
import csv
import json
import time
import datetime
from collections import deque
from typing import List, Dict, Any, Optional

from blackbox.config import BlackboxConfig
from blackbox.models import SampleData, TripEvent, TripMetadata
from dtc.database import get_dtc_info
from utils.logger import tech_logger


class TripManager:
    """Handles on-disk storage, rolling memory buffers, and event capture for a trip."""

    def __init__(self, config: Optional[BlackboxConfig] = None):
        self.config = config or BlackboxConfig()
        self.current_trip: Optional[TripMetadata] = None
        self.rolling_buffer: deque = deque()  # Holds SampleData for pre-event window
        self.active_events: List[TripEvent] = []  # Events waiting for post-samples
        self.completed_events: List[TripEvent] = []
        self.event_counter = 0

        # Incremental CSV write buffer
        self._csv_file = None
        self._csv_writer = None
        self._csv_fields = [
            "timestamp", "monotonic_ts", "RPM", "SPEED", "MAP", "TPS",
            "LOAD", "ECT", "STFT", "LTFT", "O2_B1S1", "O2_B1S2", "TIMING", "MAF", "VOLTAGE"
        ]

    def start_trip(self, port: str, elm_version: str, protocol_name: str, supported_pids: List[str]) -> TripMetadata:
        """Initializes a new trip session and sets up directory structure on disk."""
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d_%H%M%S")
        trip_id = f"VIAGEM_{timestamp_str}"

        # Create Windows-safe folder path
        trip_folder = os.path.join(self.config.storage_dir, f"{timestamp_str}_VIAGEM")
        os.makedirs(trip_folder, exist_ok=True)
        os.makedirs(os.path.join(trip_folder, "eventos"), exist_ok=True)
        os.makedirs(os.path.join(trip_folder, "logs"), exist_ok=True)

        self.current_trip = TripMetadata(
            trip_id=trip_id,
            folder_path=trip_folder,
            start_time=now.strftime("%Y-%m-%d %H:%M:%S"),
            port=port,
            elm_version=elm_version,
            protocol_name=protocol_name,
            supported_pids=supported_pids,
            status="EM_ANDAMENTO"
        )

        self.rolling_buffer.clear()
        self.active_events.clear()
        self.completed_events.clear()
        self.event_counter = 0

        # Initialize continuous CSV file
        csv_path = os.path.join(trip_folder, "dados.csv")
        self._csv_file = open(csv_path, "w", newline="", encoding="utf-8")
        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=self._csv_fields, extrasaction="ignore")
        self._csv_writer.writeheader()
        self._csv_file.flush()

        # Save initial viagem.json
        self._save_trip_json()
        tech_logger.info(f"[CAIXA-PRETA] Nova viagem iniciada: {trip_id} em {trip_folder}")
        return self.current_trip

    def add_sample(self, sample: SampleData):
        """
        Receives a continuous telemetry sample.
        Appends to rolling buffer, updates active events, and writes incrementally to disk.
        """
        if not self.current_trip:
            return

        # 1. Append to rolling buffer
        self.rolling_buffer.append(sample)

        # Prune rolling buffer to pre_event_seconds window
        cutoff = sample.monotonic_ts - self.config.pre_event_seconds
        while self.rolling_buffer and self.rolling_buffer[0].monotonic_ts < cutoff:
            self.rolling_buffer.popleft()

        # 2. Add to active post-event collection
        completed_now: List[TripEvent] = []
        for ev in self.active_events:
            ev.post_samples.append(sample)
            # Check if post-event window is complete
            if sample.monotonic_ts - ev.monotonic_ts >= self.config.post_event_seconds:
                ev.is_completed = True
                completed_now.append(ev)

        # Process newly completed events
        for ev in completed_now:
            self.active_events.remove(ev)
            self._finalize_event(ev)

        # 3. Incremental write to continuous CSV
        if self._csv_writer and self._csv_file and not self._csv_file.closed:
            try:
                row = sample.to_dict()
                self._csv_writer.writerow(row)
                self._csv_file.flush()
            except Exception as e:
                tech_logger.error(f"[CAIXA-PRETA] Erro ao gravar amostra no CSV: {str(e)}")

    def trigger_event(
        self,
        event_type: str,
        code: str,
        title: str,
        description: str,
        freeze_frame: Optional[Dict[str, Any]] = None
    ) -> TripEvent:
        """
        Triggers a new diagnostic or suspicious event.
        Captures the preceding 60 seconds from the rolling buffer and schedules 30s post-capture.
        """
        now = datetime.datetime.now()
        mono_now = time.monotonic()
        self.event_counter += 1

        safe_code = code.replace(" ", "_").replace(":", "_").replace("/", "_")
        event_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_code}_{self.event_counter:03d}"

        # Current sample
        trigger_sample = self.rolling_buffer[-1] if self.rolling_buffer else None

        # Pre-event snapshot (approx 60s)
        pre_samples = list(self.rolling_buffer)

        event = TripEvent(
            event_id=event_id,
            event_type=event_type,
            code=code,
            title=title,
            description=description,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
            monotonic_ts=mono_now,
            trigger_sample=trigger_sample,
            freeze_frame=freeze_frame or {},
            pre_samples=pre_samples,
            post_samples=[]
        )

        self.active_events.append(event)
        if self.current_trip:
            self.current_trip.events_count += 1
            if event_type == "DTC":
                self.current_trip.dtc_count += 1
            elif event_type == "COMUNICACAO":
                self.current_trip.disconnect_count += 1
            self._save_trip_json()

        tech_logger.warn(f"[CAIXA-PRETA] Evento disparado ({event_type}): {title} [{code}]")
        return event

    def _finalize_event(self, ev: TripEvent):
        """Writes completed event data to disk (evento.json, dados.csv, relatorio.html)."""
        if not self.current_trip:
            return

        folder_name = f"evento_{self.completed_events.__len__() + 1:03d}_{ev.code.replace(' ', '_')}"
        event_dir = os.path.join(self.current_trip.folder_path, "eventos", folder_name)
        os.makedirs(event_dir, exist_ok=True)
        ev.folder_path = event_dir

        # 1. Write evento.json
        with open(os.path.join(event_dir, "evento.json"), "w", encoding="utf-8") as f:
            json.dump(ev.to_dict(), f, indent=2, ensure_ascii=False)

        # 2. Write event dados.csv (60s before + trigger + 30s after)
        all_event_samples = ev.pre_samples + ev.post_samples
        with open(os.path.join(event_dir, "dados.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._csv_fields, extrasaction="ignore")
            writer.writeheader()
            for s in all_event_samples:
                writer.writerow(s.to_dict())

        # 3. Generate event HTML report
        self._generate_event_html(ev, event_dir, all_event_samples)

        self.completed_events.append(ev)
        tech_logger.success(f"[CAIXA-PRETA] Evento finalizado e salvo com buffer completo (90s): {ev.event_id}")

    def _generate_event_html(self, ev: TripEvent, event_dir: str, samples: List[SampleData]):
        """Generates self-contained HTML report with timeline analysis for the event."""
        dtc_meta = get_dtc_info(ev.code) if ev.event_type == "DTC" else None

        # Build basic summary of values at trigger moment
        trigger_vals = ev.trigger_sample.values if ev.trigger_sample else {}
        rpm = trigger_vals.get("RPM", "N/A")
        map_val = trigger_vals.get("MAP", "N/A")
        speed = trigger_vals.get("SPEED", "N/A")
        load = trigger_vals.get("LOAD", "N/A")
        tps = trigger_vals.get("TPS", "N/A")
        ect = trigger_vals.get("ECT", "N/A")
        stft = trigger_vals.get("STFT", "N/A")
        ltft = trigger_vals.get("LTFT", "N/A")

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Evento {ev.event_id} - Caixa-Preta OBD</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f1f5f9; padding: 25px; margin: 0; }}
    .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: 700; font-size: 14px; margin-bottom: 10px; }}
    .badge-dtc {{ background: #dc2626; color: white; }}
    .badge-sus {{ background: #d97706; color: white; }}
    .badge-com {{ background: #2563eb; color: white; }}
    h1 {{ margin: 0 0 10px 0; font-size: 22px; color: #38bdf8; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; }}
    .card {{ background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; }}
    .card .lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; }}
    .card .val {{ font-size: 16px; font-weight: 700; color: #f8fafc; margin-top: 4px; }}
    .advice {{ background: #0d1527; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 6px; margin: 20px 0; font-size: 13px; color: #cbd5e1; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }}
    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #0f172a; color: #94a3b8; }}
</style>
</head>
<body>
<div class="container">
    <div class="badge {'badge-dtc' if ev.event_type == 'DTC' else ('badge-sus' if ev.event_type == 'SUSPEITO' else 'badge-com')}">{ev.event_type} - {ev.code}</div>
    <h1>{ev.title}</h1>
    <div style="color: #94a3b8; font-size: 13px;">Registrado em {ev.timestamp} • Duração do buffer: {len(ev.pre_samples)} amostras antes + {len(ev.post_samples)} amostras depois</div>

    <div class="grid">
        <div class="card"><div class="lbl">RPM no Evento</div><div class="val">{rpm} rpm</div></div>
        <div class="card"><div class="lbl">MAP (Pressão Coletor)</div><div class="val">{map_val} kPa</div></div>
        <div class="card"><div class="lbl">Velocidade</div><div class="val">{speed} km/h</div></div>
        <div class="card"><div class="lbl">Carga Motor</div><div class="val">{load} %</div></div>
        <div class="card"><div class="lbl">TPS (Borboleta)</div><div class="val">{tps} %</div></div>
        <div class="card"><div class="lbl">Temp. Motor</div><div class="val">{ect} °C</div></div>
        <div class="card"><div class="lbl">STFT (Curto Prazo)</div><div class="val">{stft} %</div></div>
        <div class="card"><div class="lbl">LTFT (Longo Prazo)</div><div class="val">{ltft} %</div></div>
    </div>
"""
        if dtc_meta:
            html += f"""
    <div class="advice">
        <strong>💡 ORIENTAÇÃO NEUTRA DE DIAGNÓSTICO:</strong><br>
        {dtc_meta.neutral_advice}<br><br>
        <strong>Itens recomendados para inspeção física/elétrica:</strong>
        <ul>
            {''.join(f'<li>{c}</li>' for c in dtc_meta.checklist)}
        </ul>
    </div>
"""
        html += f"""
    <h3>Telemetria Capturada ({len(samples)} registros contínuos no arquivo dados.csv)</h3>
    <p style="color: #94a3b8; font-size: 12px;">Os dados completos de telemetria segundo a segundo estão gravados no arquivo <code>dados.csv</code> deste evento.</p>
</div>
</body>
</html>"""
        try:
            with open(os.path.join(event_dir, "relatorio.html"), "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def stop_trip(self) -> Optional[TripMetadata]:
        """Finalizes the active trip, flushes files, and marks status as FINALIZADA."""
        if not self.current_trip:
            return None

        # Flush any remaining active events (even if 30s haven't fully elapsed)
        for ev in list(self.active_events):
            ev.is_completed = True
            self._finalize_event(ev)
        self.active_events.clear()

        # Close CSV
        if self._csv_file and not self._csv_file.closed:
            self._csv_file.flush()
            self._csv_file.close()

        now = datetime.datetime.now()
        self.current_trip.end_time = now.strftime("%Y-%m-%d %H:%M:%S")

        # Calculate duration
        try:
            start_dt = datetime.datetime.strptime(self.current_trip.start_time, "%Y-%m-%d %H:%M:%S")
            self.current_trip.duration_sec = (now - start_dt).total_seconds()
        except Exception:
            pass

        self.current_trip.status = "FINALIZADA"
        self._save_trip_json()

        tech_logger.success(f"[CAIXA-PRETA] Viagem finalizada: {self.current_trip.trip_id} (Duração: {self.current_trip.duration_sec:.1f}s)")
        trip = self.current_trip
        self.current_trip = None
        return trip

    def _save_trip_json(self):
        if not self.current_trip:
            return
        json_path = os.path.join(self.current_trip.folder_path, "viagem.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.current_trip.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            tech_logger.error(f"[CAIXA-PRETA] Erro ao salvar viagem.json: {str(e)}")
