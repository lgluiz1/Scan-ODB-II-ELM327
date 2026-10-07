"""Real-time Oxygen (Lambda) Sensor Oscilloscope & Diagnostic View.
Provides high-frequency live comparison between Pre-Cat (B1S1) and Post-Cat (B1S2)
with live switching frequency detection and catalyst efficiency diagnosis (P0420).
"""
import time
from collections import deque
from typing import Optional, List, Tuple
import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QComboBox, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush, QLinearGradient,
    QPainterPath, QPolygonF
)

from obd.pids import decode_pid_value
from utils.logger import tech_logger


class O2OscilloscopeWidget(QWidget):
    """
    High-performance QPainter-based oscilloscope graph for real-time O2 sensors.
    Plots Sonda 1 (Pre-cat, Cyan) and Sonda 2 (Post-cat, Amber) against stoichiometric reference (0.45V).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.time_window = 30.0  # seconds visible on screen

        # Data buffers: (time_mono, v1, v2)
        self.data_history: deque = deque(maxlen=600)  # ~60 seconds of points at 10Hz

    def add_sample(self, v1: float, v2: float):
        now = time.monotonic()
        self.data_history.append((now, v1, v2))
        self.update()

    def clear_data(self):
        self.data_history.clear()
        self.update()

    def set_time_window(self, seconds: float):
        self.time_window = seconds
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Margins for axes
        margin_left = 54
        margin_right = 20
        margin_top = 35
        margin_bottom = 35

        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        if plot_w <= 10 or plot_h <= 10:
            return

        # 1. Background
        painter.fillRect(0, 0, w, h, QColor("#070d19"))
        painter.fillRect(margin_left, margin_top, plot_w, plot_h, QColor("#0b1326"))
        painter.setPen(QPen(QColor("#1e293b"), 1))
        painter.drawRect(margin_left, margin_top, plot_w, plot_h)

        # 2. Voltage Grid (0.0V to 1.0V)
        grid_voltages = [
            (0.0, "0.0V (Pobre)", QColor("#334155"), False),
            (0.2, "0.2V", QColor("#1e293b"), False),
            (0.45, "0.45V (λ=1.0)", QColor("#eab308"), True),  # Stoichiometric line
            (0.6, "0.6V", QColor("#1e293b"), False),
            (0.8, "0.8V", QColor("#1e293b"), False),
            (1.0, "1.0V (Rica)", QColor("#334155"), False),
        ]

        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        for v_val, label, color, is_dash in grid_voltages:
            y = margin_top + plot_h - int(v_val * plot_h)

            pen = QPen(color, 1)
            if is_dash:
                pen.setStyle(Qt.DashLine)
                pen.setWidth(1.5)
            painter.setPen(pen)
            painter.drawLine(margin_left, y, margin_left + plot_w, y)

            # Label on left axis
            painter.setPen(QColor("#94a3b8") if not is_dash else QColor("#fde047"))
            painter.drawText(6, y + 4, label)

        # 3. Time Grid markers
        now = time.monotonic()
        time_steps = [0.0, self.time_window * 0.25, self.time_window * 0.5, self.time_window * 0.75, self.time_window]
        for t_offset in time_steps:
            x = margin_left + plot_w - int((t_offset / self.time_window) * plot_w)
            if margin_left <= x <= margin_left + plot_w:
                painter.setPen(QPen(QColor("#1e293b"), 1, Qt.DotLine))
                painter.drawLine(x, margin_top, x, margin_top + plot_h)

                painter.setPen(QColor("#64748b"))
                label_t = f"-{int(t_offset)}s" if t_offset > 0 else "Agora"
                painter.drawText(x - 14, margin_top + plot_h + 18, label_t)

        # 4. Plot Curves
        if len(self.data_history) > 1:
            poly_s1 = QPolygonF()
            poly_s2 = QPolygonF()

            cutoff_mono = now - self.time_window

            for t_mono, v1, v2 in self.data_history:
                if t_mono < cutoff_mono:
                    continue

                # Coordinate X (0 at now, -time_window at left)
                time_diff = now - t_mono
                x = margin_left + plot_w - int((time_diff / self.time_window) * plot_w)

                # Clamp voltages to [0.0, 1.0]
                clamped_v1 = max(0.0, min(1.0, v1))
                clamped_v2 = max(0.0, min(1.0, v2))

                y1 = margin_top + plot_h - int(clamped_v1 * plot_h)
                y2 = margin_top + plot_h - int(clamped_v2 * plot_h)

                poly_s1.append(QPointF(x, y1))
                poly_s2.append(QPointF(x, y2))

            # Draw Sonda 2 (Post-cat, Orange/Amber)
            if not poly_s2.isEmpty():
                pen_s2 = QPen(QColor("#fb923c"), 2.2)
                pen_s2.setCapStyle(Qt.RoundCap)
                pen_s2.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen_s2)
                painter.drawPolyline(poly_s2)

            # Draw Sonda 1 (Pre-cat, Cyan)
            if not poly_s1.isEmpty():
                pen_s1 = QPen(QColor("#38bdf8"), 2.5)
                pen_s1.setCapStyle(Qt.RoundCap)
                pen_s1.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen_s1)
                painter.drawPolyline(poly_s1)

        # 5. Top Header Legend (Adaptive positioning)
        legend_font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(legend_font)

        t1 = "Sonda 1 (Pré-Cat / B1S1) — Mistura"
        painter.fillRect(margin_left + 10, 10, 11, 11, QColor("#38bdf8"))
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(margin_left + 26, 20, t1)

        fm = painter.fontMetrics()
        w1 = fm.horizontalAdvance(t1)

        t2 = "Sonda 2 (Pós-Cat / B1S2) — Catalisador"
        s2_x = margin_left + 10 + w1 + 25
        if s2_x + 160 <= w - margin_right:
            painter.fillRect(s2_x, 10, 11, 11, QColor("#fb923c"))
            painter.setPen(QColor("#e2e8f0"))
            painter.drawText(s2_x + 16, 20, t2)


class LambdaWorker(QThread):
    """
    Dedicated background worker thread for high-frequency acquisition of O2 sensor PIDs (0114, 0115, 0124).
    """
    sample_received = Signal(float, float, float)  # v1, v2, lambda_val
    error_occurred = Signal(str)

    def __init__(self, connection):
        super().__init__()
        self.conn = connection
        self._running = False
        self._paused = False

    def run(self):
        self._running = True
        tech_logger.info("[LAMBDA] Iniciando aquisição contínua das sondas de oxigênio...")

        while self._running:
            if self._paused or not self.conn or not self.conn.is_connected:
                time.sleep(0.1)
                continue

            cycle_start = time.monotonic()

            # 1. Query S1 (PID 0114)
            v1 = 0.45
            ok1, resp1 = self.conn.send_raw_command("0114", timeout=0.8)
            if ok1 and resp1:
                decoded_v1 = decode_pid_value("0114", resp1)
                if decoded_v1 is not None and isinstance(decoded_v1, (int, float)):
                    v1 = float(decoded_v1)

            # 2. Query S2 (PID 0115)
            v2 = 0.55
            ok2, resp2 = self.conn.send_raw_command("0115", timeout=0.8)
            if ok2 and resp2:
                decoded_v2 = decode_pid_value("0115", resp2)
                if decoded_v2 is not None and isinstance(decoded_v2, (int, float)):
                    v2 = float(decoded_v2)

            # 3. Query Lambda ratio (PID 0124) - if supported
            lam = 1.000
            ok_l, resp_l = self.conn.send_raw_command("0124", timeout=0.8)
            if ok_l and resp_l:
                decoded_l = decode_pid_value("0124", resp_l)
                if decoded_l is not None and isinstance(decoded_l, (int, float)):
                    lam = float(decoded_l)

            self.sample_received.emit(v1, v2, lam)

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.04, 0.12 - elapsed)  # Target ~8-10 samples per second
            time.sleep(sleep_time)

        tech_logger.info("[LAMBDA] Aquisição das sondas finalizada.")

    def stop(self):
        self._running = False
        self.wait(2000)

    def set_paused(self, paused: bool):
        self._paused = paused


class LambdaView(QWidget):
    """
    Dedicated Dashboard for Oxygen / Lambda Sensors inspection and diagnosis.
    Compares Pre-Cat vs Post-Cat sensor waveforms to analyze catalyst efficiency and AFR control.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[LambdaWorker] = None
        self.conn = None
        self.is_running = False

        # Metrics history for frequency / status computation
        self.s1_recent: deque = deque(maxlen=40)
        self.s2_recent: deque = deque(maxlen=40)
        self.s1_crossings = 0
        self.last_cross_mono = 0.0

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
        layout.setSpacing(10)

        # 1. Header Bar
        hdr_frame = QFrame()
        hdr_frame.setObjectName("lambdaHdrFrame")
        hdr_frame.setStyleSheet("""
            QFrame#lambdaHdrFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        h_box = QHBoxLayout(hdr_frame)
        h_box.setContentsMargins(12, 8, 12, 8)
        h_box.setSpacing(10)

        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        lbl_t = QLabel("📈 MONITORAMENTO DAS SONDAS LAMBDA (O2)")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 800; color: #38bdf8; background: transparent;")
        lbl_sub = QLabel("Osciloscópio de sinal em tempo real • Análise de mistura e eficiência do catalisador (P0420)")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        t_box.addWidget(lbl_t)
        t_box.addWidget(lbl_sub)
        h_box.addLayout(t_box)

        h_box.addStretch()

        # Controls
        lbl_win = QLabel("Janela:")
        lbl_win.setStyleSheet("font-size: 12px; color: #cbd5e1; font-weight: 600; background: transparent;")
        h_box.addWidget(lbl_win)

        self.combo_window = QComboBox()
        self.combo_window.addItem("15 segundos", 15.0)
        self.combo_window.addItem("30 segundos", 30.0)
        self.combo_window.addItem("60 segundos", 60.0)
        self.combo_window.setCurrentIndex(1)
        self.combo_window.currentIndexChanged.connect(self._change_window)
        h_box.addWidget(self.combo_window)

        self.btn_toggle = QPushButton("▶ INICIAR LEITURA DAS SONDAS")
        self.btn_toggle.setObjectName("successBtn")
        self.btn_toggle.setStyleSheet("font-weight: 700; padding: 6px 14px; font-size: 12px;")
        self.btn_toggle.clicked.connect(self._toggle_acquisition)
        h_box.addWidget(self.btn_toggle)

        self.btn_clear = QPushButton("🗑️ Limpar")
        self.btn_clear.setObjectName("secondaryBtn")
        self.btn_clear.setStyleSheet("padding: 6px 12px; font-size: 12px;")
        self.btn_clear.clicked.connect(self._clear_graph)
        h_box.addWidget(self.btn_clear)

        layout.addWidget(hdr_frame)

        # 2. Key Diagnostic Cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)

        # Card S1 (Pré-Catalisador)
        self.card_s1 = self._create_card(
            title="SONDA 1 (PRÉ-CAT / B1S1)",
            value="0.00 V",
            val_color="#38bdf8",
            status="Aguardando início...",
            status_color="#94a3b8"
        )
        cards_layout.addWidget(self.card_s1, 0, 0)

        # Card S2 (Pós-Catalisador)
        self.card_s2 = self._create_card(
            title="SONDA 2 (PÓS-CAT / B1S2)",
            value="0.00 V",
            val_color="#fb923c",
            status="Aguardando início...",
            status_color="#94a3b8"
        )
        cards_layout.addWidget(self.card_s2, 0, 1)

        # Card Diagnosis (Eficiência / P0420)
        self.card_diag = self._create_card(
            title="DIAGNÓSTICO DO CATALISADOR",
            value="EM ANÁLISE",
            val_color="#a855f7",
            status="Aguardando amostragem contínua para comparação das sondas.",
            status_color="#cbd5e1"
        )
        cards_layout.addWidget(self.card_diag, 0, 2)

        layout.addLayout(cards_layout)

        # 3. Oscilloscope Chart
        self.oscilloscope = O2OscilloscopeWidget()
        self.oscilloscope.setMinimumHeight(280)
        layout.addWidget(self.oscilloscope, stretch=1)

        # 4. Technical Diagnosis Guide
        guide_frame = QFrame()
        guide_frame.setObjectName("guideFrame")
        guide_frame.setStyleSheet("""
            QFrame#guideFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        g_box = QVBoxLayout(guide_frame)
        g_box.setContentsMargins(12, 8, 12, 8)
        g_box.setSpacing(4)

        lbl_g_hdr = QLabel("💡 Como interpretar o comportamento das sondas no seu Logan:")
        lbl_g_hdr.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 12px; background: transparent;")
        g_box.addWidget(lbl_g_hdr)

        lbl_g1 = QLabel("• <b>Sonda 1 (Pré-Cat / Ciano):</b> Deve oscilar ativamente entre <b>0.1V e 0.9V</b> (chaveamento rápido em malha fechada). Se ficar travada abaixo de 0.2V (pobre) ou acima de 0.8V (rica), há anomalia de mistura ou fuga de ar/MAP.")
        lbl_g1.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent;")
        lbl_g1.setWordWrap(True)
        g_box.addWidget(lbl_g1)

        lbl_g2 = QLabel("• <b>Sonda 2 (Pós-Cat / Laranja):</b> Deve manter-se <b>estável em torno de 0.55V a 0.65V</b>. Se a Sonda 2 começar a oscilar sincronizada com a Sonda 1, indica perda de retenção de oxigênio do catalisador (origem do código <b>P0420</b>).")
        lbl_g2.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent;")
        lbl_g2.setWordWrap(True)
        g_box.addWidget(lbl_g2)

        layout.addWidget(guide_frame)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_card(self, title: str, value: str, val_color: str, status: str, status_color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("diagCard")
        card.setStyleSheet("""
            QFrame#diagCard {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 8px;
            }
        """)
        card.setMinimumHeight(80)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(3)

        t = QLabel(title)
        t.setStyleSheet("font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; background: transparent;")
        v.addWidget(t)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("cardVal")
        val_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {val_color}; background: transparent;")
        v.addWidget(val_lbl)

        st_lbl = QLabel(status)
        st_lbl.setObjectName("cardStatus")
        st_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {status_color}; background: transparent;")
        st_lbl.setWordWrap(True)
        v.addWidget(st_lbl)

        return card

    def _set_card_state(self, card: QFrame, state: str):
        """
        Dynamically adjusts card container styling and glowing borders based on state:
        'good' -> emerald border
        'warning' -> amber border
        'danger' -> bright red border with wine background
        'normal' -> slate border
        """
        if state == "good":
            card.setStyleSheet("""
                QFrame#diagCard {
                    background-color: #0b1f24;
                    border: 1.5px solid #10b981;
                    border-radius: 8px;
                }
            """)
        elif state == "warning":
            card.setStyleSheet("""
                QFrame#diagCard {
                    background-color: #241a0b;
                    border: 1.5px solid #f59e0b;
                    border-radius: 8px;
                }
            """)
        elif state == "danger":
            card.setStyleSheet("""
                QFrame#diagCard {
                    background-color: #260c10;
                    border: 2px solid #ef4444;
                    border-radius: 8px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#diagCard {
                    background-color: #131c2e;
                    border: 1px solid #233149;
                    border-radius: 8px;
                }
            """)

    def set_connection(self, conn):
        self.conn = conn

    def _change_window(self):
        val = self.combo_window.currentData()
        if val:
            self.oscilloscope.set_time_window(float(val))

    def _clear_graph(self):
        self.oscilloscope.clear_data()
        self.s1_recent.clear()
        self.s2_recent.clear()

    def _toggle_acquisition(self):
        if not self.conn or not self.conn.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao adaptador antes de iniciar a leitura das sondas.")
            return

        if not self.is_running:
            # Start worker
            self.is_running = True
            self.btn_toggle.setText("⏸ PAUSAR LEITURA")
            self.btn_toggle.setObjectName("dangerBtn")
            self.btn_toggle.setStyleSheet("font-weight: 700; padding: 8px 18px;")

            self.worker = LambdaWorker(self.conn)
            self.worker.sample_received.connect(self._on_sample_received)
            self.worker.start()
        else:
            # Stop worker
            self.is_running = False
            self.btn_toggle.setText("▶ RETOMAR LEITURA")
            self.btn_toggle.setObjectName("successBtn")
            self.btn_toggle.setStyleSheet("font-weight: 700; padding: 8px 18px;")

            if self.worker:
                self.worker.stop()
                self.worker = None

    def _on_sample_received(self, v1: float, v2: float, lam: float):
        try:
            self.oscilloscope.add_sample(v1, v2)
            self.s1_recent.append(v1)
            self.s2_recent.append(v2)

            # Update S1 Card
            lbl_v1 = self.card_s1.findChild(QLabel, "cardVal")
            if lbl_v1:
                lbl_v1.setText(f"{v1:.3f} V")

            lbl_st1 = self.card_s1.findChild(QLabel, "cardStatus")
            if lbl_st1:
                if len(self.s1_recent) >= 10:
                    min_1 = min(self.s1_recent)
                    max_1 = max(self.s1_recent)
                    delta_1 = max_1 - min_1
                    if delta_1 > 0.40:
                        lbl_st1.setText(f"🟢 Chaveamento Ativo ({min_1:.2f}V - {max_1:.2f}V)")
                        lbl_st1.setStyleSheet("font-size: 11px; font-weight: 600; color: #34d399; background: transparent;")
                        self._set_card_state(self.card_s1, "good")
                    elif v1 < 0.25:
                        lbl_st1.setText("⚠️ Travada em Mistura Pobre (<0.25V)")
                        lbl_st1.setStyleSheet("font-size: 11px; font-weight: 600; color: #ef4444; background: transparent;")
                        self._set_card_state(self.card_s1, "danger")
                    elif v1 > 0.75:
                        lbl_st1.setText("⚠️ Travada em Mistura Rica (>0.75V)")
                        lbl_st1.setStyleSheet("font-size: 11px; font-weight: 600; color: #fbbf24; background: transparent;")
                        self._set_card_state(self.card_s1, "warning")
                    else:
                        lbl_st1.setText(f"Sinal Intermediário ({min_1:.2f}V - {max_1:.2f}V)")
                        lbl_st1.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8; background: transparent;")
                        self._set_card_state(self.card_s1, "normal")

            # Update S2 Card
            lbl_v2 = self.card_s2.findChild(QLabel, "cardVal")
            if lbl_v2:
                lbl_v2.setText(f"{v2:.3f} V")

            lbl_st2 = self.card_s2.findChild(QLabel, "cardStatus")
            if lbl_st2:
                if len(self.s2_recent) >= 10:
                    min_2 = min(self.s2_recent)
                    max_2 = max(self.s2_recent)
                    delta_2 = max_2 - min_2
                    if delta_2 < 0.20 and 0.45 <= v2 <= 0.75:
                        lbl_st2.setText(f"🟢 Sinal Estável no Catalisador ({delta_2:.2f}V variação)")
                        lbl_st2.setStyleSheet("font-size: 11px; font-weight: 600; color: #34d399; background: transparent;")
                        self._set_card_state(self.card_s2, "good")
                    elif delta_2 >= 0.35:
                        lbl_st2.setText(f"⚠️ Atenção: Oscilando ({delta_2:.2f}V variação)")
                        lbl_st2.setStyleSheet("font-size: 11px; font-weight: 600; color: #f97316; background: transparent;")
                        self._set_card_state(self.card_s2, "warning")
                    else:
                        lbl_st2.setText(f"Estabilidade normal ({min_2:.2f}V - {max_2:.2f}V)")
                        lbl_st2.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8; background: transparent;")
                        self._set_card_state(self.card_s2, "normal")

            # Update Diagnosis Card
            lbl_diag_v = self.card_diag.findChild(QLabel, "cardVal")
            lbl_diag_st = self.card_diag.findChild(QLabel, "cardStatus")
            if lbl_diag_v and lbl_diag_st and len(self.s1_recent) >= 20 and len(self.s2_recent) >= 20:
                delta_1 = max(self.s1_recent) - min(self.s1_recent)
                delta_2 = max(self.s2_recent) - min(self.s2_recent)

                if delta_1 > 0.45 and delta_2 < 0.25:
                    lbl_diag_v.setText("CATALISADOR SAUDÁVEL")
                    lbl_diag_v.setStyleSheet("font-size: 19px; font-weight: 800; color: #34d399; background: transparent;")
                    lbl_diag_st.setText("A S1 oscila com a combustão e a S2 permanece estável. Retenção de O2 íntegra.")
                    self._set_card_state(self.card_diag, "good")
                elif delta_1 > 0.40 and delta_2 >= 0.35:
                    lbl_diag_v.setText("⚠️ BAIXA EFICIÊNCIA (P0420)")
                    lbl_diag_v.setStyleSheet("font-size: 19px; font-weight: 800; color: #ef4444; background: transparent;")
                    lbl_diag_st.setText("A S2 está oscilando junto com a S1. O catalisador não está retendo oxigênio adequadamente.")
                    self._set_card_state(self.card_diag, "danger")
                else:
                    lbl_diag_v.setText("AQUECIMENTO / MONITORANDO")
                    lbl_diag_v.setStyleSheet("font-size: 19px; font-weight: 800; color: #a855f7; background: transparent;")
                    lbl_diag_st.setText(f"Equivalência Lambda instantânea: λ = {lam:.3f}")
                    self._set_card_state(self.card_diag, "normal")
        except Exception:
            pass

    def stop_monitoring(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.is_running = False
        self.btn_toggle.setText("▶ INICIAR LEITURA DAS SONDAS")
        self.btn_toggle.setObjectName("successBtn")
