"""Minimalist, distraction-free Blackbox (Modo Viagem) driver dashboard.
Designed for hands-free operation while driving.
"""
import time
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from blackbox.models import TripEvent, TripMetadata


class BlackboxView(QWidget):
    """
    Hands-free dashboard for Blackbox trip monitoring.
    Displays clear, large visual indicators of connection, engine, timer, and last event.
    """

    def __init__(
        self,
        on_start_trip: Callable[[], None],
        on_pause_trip: Callable[[bool], None],
        on_stop_trip: Callable[[], None],
        parent=None
    ):
        super().__init__(parent)
        self.on_start_trip = on_start_trip
        self.on_pause_trip = on_pause_trip
        self.on_stop_trip = on_stop_trip

        self.is_monitoring = False
        self.is_paused = False
        self.trip_start_mono: Optional[float] = None

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_timer)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # 1. Header Banner
        hdr_frame = QFrame()
        hdr_frame.setObjectName("bbHdrFrame")
        hdr_frame.setStyleSheet("""
            QFrame#bbHdrFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        h_box = QHBoxLayout(hdr_frame)
        h_box.setContentsMargins(12, 8, 12, 8)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        lbl_title = QLabel("🚗 CAIXA-PRETA DO VEÍCULO — MODO VIAGEM")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; background: transparent;")
        title_v.addWidget(lbl_title)

        lbl_desc = QLabel("Gravação contínua segundo a segundo • Buffer circular (60s pré-evento + 30s pós-evento)")
        lbl_desc.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        title_v.addWidget(lbl_desc)
        h_box.addLayout(title_v)

        h_box.addStretch()

        self.lbl_trip_state = QLabel("⚪ AGUARDANDO INÍCIO")
        self.lbl_trip_state.setStyleSheet("""
            background-color: #1e293b;
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 14px;
            border: 1px solid #334155;
        """)
        h_box.addWidget(self.lbl_trip_state)
        layout.addWidget(hdr_frame)

        # 2. Key Metrics Grid (Large, high readability from distance)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(10)

        # Card 1: Timer
        self.card_timer = self._create_metric_card("TEMPO DECORRIDO", "00:00:00", "#38bdf8")
        metrics_grid.addWidget(self.card_timer, 0, 0)

        # Card 2: Engine State
        self.card_engine = self._create_metric_card("ESTADO DO MOTOR", "AGUARDANDO", "#94a3b8")
        metrics_grid.addWidget(self.card_engine, 0, 1)

        # Card 3: DTCs Count
        self.card_dtcs = self._create_metric_card("DTCs CONFIRMADOS", "0", "#10b981")
        metrics_grid.addWidget(self.card_dtcs, 0, 2)

        # Card 4: Events Count
        self.card_events = self._create_metric_card("TOTAL DE EVENTOS", "0", "#cbd5e1")
        metrics_grid.addWidget(self.card_events, 0, 3)

        layout.addLayout(metrics_grid)

        # 3. Last Event Display Banner
        self.event_banner = QFrame()
        self.event_banner.setObjectName("eventBanner")
        self.event_banner.setStyleSheet("""
            QFrame#eventBanner {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        ev_box = QVBoxLayout(self.event_banner)
        ev_box.setContentsMargins(14, 10, 14, 10)
        ev_box.setSpacing(4)

        ev_header = QHBoxLayout()
        ev_title = QLabel("ÚLTIMO EVENTO CAPTURADO")
        ev_title.setStyleSheet("font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 0.5px;")
        ev_header.addWidget(ev_title)
        ev_header.addStretch()

        self.lbl_ev_badge = QLabel("NENHUM EVENTO")
        self.lbl_ev_badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; background: #1e293b; padding: 2px 8px; border-radius: 4px;")
        ev_header.addWidget(self.lbl_ev_badge)
        ev_box.addLayout(ev_header)

        self.lbl_ev_detail = QLabel("O sistema está monitorando ativamente. Nenhuma anomalia ou DTC detectado até o momento.")
        self.lbl_ev_detail.setWordWrap(True)
        self.lbl_ev_detail.setStyleSheet("font-size: 13px; font-weight: 600; color: #f1f5f9; margin-top: 4px;")
        ev_box.addWidget(self.lbl_ev_detail)

        layout.addWidget(self.event_banner)

        # 4. Telemetry Strip (Live Values)
        self.telemetry_strip = QFrame()
        self.telemetry_strip.setObjectName("telemetryStrip")
        self.telemetry_strip.setStyleSheet("""
            QFrame#telemetryStrip {
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        self.telemetry_strip.setMinimumHeight(55)
        t_box = QHBoxLayout(self.telemetry_strip)
        t_box.setContentsMargins(10, 6, 10, 6)

        self.lbl_live_rpm = self._create_strip_item("RPM", "--", "rpm")
        t_box.addLayout(self.lbl_live_rpm)

        self.lbl_live_speed = self._create_strip_item("VELOCIDADE", "--", "km/h")
        t_box.addLayout(self.lbl_live_speed)

        self.lbl_live_map = self._create_strip_item("MAP", "--", "kPa")
        t_box.addLayout(self.lbl_live_map)

        self.lbl_live_tps = self._create_strip_item("TPS", "--", "%")
        t_box.addLayout(self.lbl_live_tps)

        self.lbl_live_ect = self._create_strip_item("TEMP MOTOR", "--", "°C")
        t_box.addLayout(self.lbl_live_ect)

        self.lbl_live_stft = self._create_strip_item("STFT", "--", "%")
        t_box.addLayout(self.lbl_live_stft)

        self.lbl_live_cycle = self._create_strip_item("CICLO", "--", "ms")
        t_box.addLayout(self.lbl_live_cycle)

        layout.addWidget(self.telemetry_strip)

        layout.addStretch()

        # 5. Bottom Action Controls
        ctrl_box = QHBoxLayout()
        ctrl_box.setSpacing(14)

        self.btn_start = QPushButton("🚗 INICIAR MODO VIAGEM")
        self.btn_start.setObjectName("successBtn")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setStyleSheet("font-size: 13px; font-weight: 700; padding: 8px 20px;")
        self.btn_start.clicked.connect(self._handle_start)
        ctrl_box.addWidget(self.btn_start)

        self.btn_pause = QPushButton("⏸️ PAUSAR")
        self.btn_pause.setObjectName("secondaryBtn")
        self.btn_pause.setMinimumHeight(40)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setStyleSheet("font-size: 12px; font-weight: 600; padding: 8px 16px;")
        self.btn_pause.clicked.connect(self._handle_pause)
        ctrl_box.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹️ ENCERRAR VIAGEM")
        self.btn_stop.setObjectName("dangerBtn")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("font-size: 12px; font-weight: 700; padding: 8px 20px;")
        self.btn_stop.clicked.connect(self._handle_stop)
        ctrl_box.addWidget(self.btn_stop)

        ctrl_box.addStretch()

        lbl_handsfree = QLabel("🛡️ Mãos livres: grava automaticamente sem necessidade de cliques ao dirigir.")
        lbl_handsfree.setStyleSheet("color: #64748b; font-size: 12px;")
        ctrl_box.addWidget(lbl_handsfree)

        layout.addLayout(ctrl_box)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_metric_card(self, title: str, initial_val: str, val_color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        card.setStyleSheet("""
            QFrame#metricCard {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 8px;
            }
        """)
        card.setMinimumHeight(75)
        v = QVBoxLayout(card)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(3)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
        v.addWidget(lbl_t)

        lbl_v = QLabel(initial_val)
        lbl_v.setObjectName("metricVal")
        lbl_v.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {val_color}; background: transparent;")
        v.addWidget(lbl_v)

        return card

    def _create_strip_item(self, label: str, init_val: str, unit: str) -> QVBoxLayout:
        v = QVBoxLayout()
        v.setSpacing(2)
        v.setContentsMargins(4, 0, 4, 0)

        lbl_hdr = QLabel(label)
        lbl_hdr.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 700;")
        v.addWidget(lbl_hdr)

        lbl_data = QLabel(f"{init_val} {unit}")
        lbl_data.setObjectName("stripVal")
        lbl_data.setStyleSheet("font-size: 13px; font-weight: 700; color: #e2e8f0;")
        v.addWidget(lbl_data)

        return v

    def set_trip_started(self, trip_id: str):
        self.is_monitoring = True
        self.is_paused = False
        self.trip_start_mono = time.monotonic()

        self.lbl_trip_state.setText("🟢 MONITORAMENTO ATIVO")
        self.lbl_trip_state.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            font-size: 12px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 16px;
            border: 1px solid #059669;
        """)

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setText("⏸️ PAUSAR")

        self._timer.start()

    def set_trip_stopped(self):
        self.is_monitoring = False
        self.is_paused = False
        self._timer.stop()

        self.lbl_trip_state.setText("⚪ VIAGEM FINALIZADA")
        self.lbl_trip_state.setStyleSheet("""
            background-color: #1e293b;
            color: #94a3b8;
            font-size: 12px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 16px;
            border: 1px solid #334155;
        """)

        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def update_telemetry(self, sample):
        try:
            vals = sample.values
            if "RPM" in vals and vals["RPM"] is not None:
                self._update_strip_text(self.lbl_live_rpm, str(vals["RPM"]), "rpm")
            if "SPEED" in vals and vals["SPEED"] is not None:
                self._update_strip_text(self.lbl_live_speed, str(vals["SPEED"]), "km/h")
            if "MAP" in vals and vals["MAP"] is not None:
                self._update_strip_text(self.lbl_live_map, str(vals["MAP"]), "kPa")
            if "TPS" in vals and vals["TPS"] is not None:
                self._update_strip_text(self.lbl_live_tps, str(vals["TPS"]), "%")
            if "ECT" in vals and vals["ECT"] is not None:
                self._update_strip_text(self.lbl_live_ect, str(vals["ECT"]), "°C")
            if "STFT" in vals and vals["STFT"] is not None:
                stft_val = vals["STFT"]
                stft_str = f"{stft_val:+}" if isinstance(stft_val, (int, float)) else str(stft_val)
                self._update_strip_text(self.lbl_live_stft, stft_str, "%")
        except Exception:
            pass

    def _update_strip_text(self, v_layout: QVBoxLayout, val_str: str, unit: str):
        try:
            item = v_layout.itemAt(1)
            if item and item.widget():
                item.widget().setText(f"{val_str} {unit}")
        except Exception:
            pass

    def update_status(self, data: dict):
        try:
            engine_str = data.get("engine", "DESCONHECIDO")
            if engine_str == "FUNCIONANDO":
                self._set_card_val(self.card_engine, "🟢 FUNCIONANDO", "#34d399")
            elif engine_str == "PARADO":
                self._set_card_val(self.card_engine, "🟡 MOTOR PARADO", "#fbbf24")
            else:
                self._set_card_val(self.card_engine, "⚪ ECU DESLIGADA", "#94a3b8")

            self._set_card_val(self.card_dtcs, str(data.get("dtc_count", 0)), "#ef4444" if data.get("dtc_count", 0) > 0 else "#10b981")
            self._set_card_val(self.card_events, str(data.get("events_count", 0)), "#38bdf8")

            cycle_ms = data.get("cycle_ms", 0)
            self._update_strip_text(self.lbl_live_cycle, str(cycle_ms), "ms")
        except Exception:
            pass

    def display_event(self, ev: TripEvent):
        # Update event banner
        if ev.event_type == "DTC":
            self.lbl_ev_badge.setText(f"🟥 DTC {ev.code}")
            self.lbl_ev_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: white; background: #dc2626; padding: 3px 10px; border-radius: 4px;")
            self.event_banner.setStyleSheet("""
                QFrame#eventBanner {
                    background-color: #2b1318;
                    border: 1px solid #dc2626;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        elif ev.event_type == "SUSPEITO":
            self.lbl_ev_badge.setText(f"🟨 SUSPEITO {ev.code}")
            self.lbl_ev_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: white; background: #d97706; padding: 3px 10px; border-radius: 4px;")
            self.event_banner.setStyleSheet("""
                QFrame#eventBanner {
                    background-color: #2b2613;
                    border: 1px solid #d97706;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
        else:
            self.lbl_ev_badge.setText(f"🟦 COMUNICAÇÃO")
            self.lbl_ev_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: white; background: #2563eb; padding: 3px 10px; border-radius: 4px;")
            self.event_banner.setStyleSheet("""
                QFrame#eventBanner {
                    background-color: #172554;
                    border: 1px solid #2563eb;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)

        self.lbl_ev_detail.setText(f"[{ev.timestamp}] {ev.title}: {ev.description}")

    def _set_card_val(self, card_frame: QFrame, val_str: str, color: str):
        lbl = card_frame.findChild(QLabel, "metricVal")
        if lbl:
            lbl.setText(val_str)
            lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color};")

    def _update_timer(self):
        if self.is_monitoring and not self.is_paused and self.trip_start_mono:
            elapsed = int(time.monotonic() - self.trip_start_mono)
            hrs = elapsed // 3600
            mins = (elapsed % 3600) // 60
            secs = elapsed % 60
            time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            self._set_card_val(self.card_timer, time_str, "#38bdf8")

    def _handle_start(self):
        self.on_start_trip()

    def _handle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.setText("▶️ RETOMAR" if self.is_paused else "⏸️ PAUSAR")
        self.lbl_trip_state.setText("🟡 VIAGEM PAUSADA" if self.is_paused else "🟢 MONITORAMENTO ATIVO")
        self.on_pause_trip(self.is_paused)

    def _handle_stop(self):
        ans = QMessageBox.question(
            self,
            "Encerrar Viagem",
            "Deseja encerrar a gravação da viagem e gerar o resumo final?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.on_stop_trip()
