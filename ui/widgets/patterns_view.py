"""Statistical pattern analysis across captured Blackbox events.
Provides objective telemetry correlations without prescriptive mechanical conclusions.
"""
import os
import json
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextBrowser, QMessageBox
)
from PySide6.QtCore import Qt
from blackbox.config import BASE_STORAGE_DIR
from database.db import db


class PatternsView(QWidget):
    """Aggregates sensor metrics across multiple trip events to identify operating conditions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header
        hdr_box = QHBoxLayout()
        lbl_title = QLabel("📊 Análise de Padrões Operacionais (Condições dos Eventos)")
        lbl_title.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        hdr_box.addWidget(lbl_title)
        hdr_box.addStretch()

        self.btn_analyze = QPushButton("⚡ Processar Padrões")
        self.btn_analyze.clicked.connect(self.run_analysis)
        hdr_box.addWidget(self.btn_analyze)

        layout.addLayout(hdr_box)

        # Summary Frame
        self.summary_box = QTextBrowser()
        self.summary_box.setOpenExternalLinks(True)
        self.summary_box.setStyleSheet("""
            QTextBrowser {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 8px;
                padding: 16px;
                color: #e2e8f0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.summary_box)

        self._show_empty_state()

    def _show_empty_state(self):
        self.summary_box.setHtml("""
            <div style="text-align: center; color: #64748b; padding: 40px;">
                <h3 style="color: #94a3b8;">Nenhuma análise realizada ainda</h3>
                <p>Clique em <b>'Processar Padrões'</b> para correlacionar as condições de motor (RPM, MAP, carga e trims) em que os eventos ocorreram.</p>
            </div>
        """)

    def run_analysis(self):
        events = db.list_trip_events()
        if not events:
            self._show_empty_state()
            return

        total_events = len(events)
        dtc_events = [e for e in events if e.get("event_type") == "DTC"]
        sus_events = [e for e in events if e.get("event_type") == "SUSPEITO"]

        # Read evento.json from available folders to inspect trigger samples
        rpms = []
        maps = []
        tps_list = []
        stfts = []

        for e in events:
            folder = e.get("folder_path")
            if folder and os.path.exists(folder):
                json_p = os.path.join(folder, "evento.json")
                if os.path.exists(json_p):
                    try:
                        with open(json_p, "r", encoding="utf-8") as f:
                            edata = json.load(f)
                            # inspect trigger or pre_samples
                            tsamp = edata.get("trigger_sample") or (edata.get("pre_samples")[-1] if edata.get("pre_samples") else None)
                            if tsamp:
                                vals = tsamp.get("values", {})
                                if "RPM" in vals: rpms.append(vals["RPM"])
                                if "MAP" in vals: maps.append(vals["MAP"])
                                if "TPS" in vals: tps_list.append(vals["TPS"])
                                if "STFT" in vals: stfts.append(vals["STFT"])
                    except Exception:
                        pass

        # Build statistical insights
        insights = []
        if rpms:
            avg_rpm = sum(rpms) / len(rpms)
            low_rpm_count = sum(1 for r in rpms if r < 2000)
            pct_low = (low_rpm_count / len(rpms)) * 100
            if pct_low >= 50:
                insights.append(f"• <b>Faixa de Rotação:</b> {pct_low:.0f}% dos eventos ocorreram em <b>baixa rotação (&lt; 2.000 rpm)</b>, com média de <b>{avg_rpm:.0f} rpm</b>.")

        if maps:
            avg_map = sum(maps) / len(maps)
            high_map_count = sum(1 for m in maps if m >= 75)
            pct_high_map = (high_map_count / len(maps)) * 100
            if pct_high_map >= 40:
                insights.append(f"• <b>Pressão no Coletor (MAP):</b> {pct_high_map:.0f}% dos eventos ocorreram com <b>MAP elevado (&ge; 75 kPa)</b>, com média de <b>{avg_map:.0f} kPa</b> (típico de condição de subida ou motor sob esforço).")

        if tps_list:
            avg_tps = sum(tps_list) / len(tps_list)
            high_tps_count = sum(1 for t in tps_list if t >= 50)
            pct_tps = (high_tps_count / len(tps_list)) * 100
            if pct_tps >= 40:
                insights.append(f"• <b>Abertura de Borboleta (TPS):</b> {pct_tps:.0f}% dos eventos ocorreram com aceleração moderada a alta (&ge; 50%), média de <b>{avg_tps:.1f}%</b>.")

        if stfts:
            avg_stft = sum(stfts) / len(stfts)
            if avg_stft > 5.0:
                insights.append(f"• <b>Correção de Mistura (STFT):</b> Ajuste de combustível positivo médio de <b>{avg_stft:+.1f}%</b> no momento dos eventos (a ECU estava enriquecendo a mistura).")

        if not insights:
            insights.append("• Os eventos registrados possuem dispersão variada de parâmetros sem concentração estatística acentuada até o momento.")

        insights_html = "<br>".join(insights)

        html = f"""
        <div style="font-family: sans-serif;">
            <h2 style="color: #38bdf8; margin-top: 0;">Análise Estatística de Padrões Operacionais</h2>
            <p style="color: #94a3b8; font-size: 13px;">
                Total de eventos analisados: <b>{total_events}</b> (<b>{len(dtc_events)}</b> DTCs confirmados, <b>{len(sus_events)}</b> eventos suspeitos).
            </p>

            <div style="background-color: #0f172a; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <h4 style="color: #60a5fa; margin: 0 0 8px 0;">CONDIÇÕES PREDOMINANTES CONSTATADAS:</h4>
                <div style="color: #e2e8f0; font-size: 13px; line-height: 1.6;">
                    {insights_html}
                </div>
            </div>

            <div style="background: #1e1b4b; border: 1px solid #4338ca; padding: 12px; border-radius: 6px; color: #cbd5e1; font-size: 12px;">
                <b>ℹ️ NOTA METODOLÓGICA:</b> Esta análise expressa correlações estatísticas entre as variáveis lidas pela ECU e os instantes das ocorrências. Ela <u>não substitui</u> a análise com osciloscópio, manômetro de combustível e inspeção visual do chicote elétrico e estanqueidade do coletor.
            </div>
        </div>
        """
        self.summary_box.setHtml(html)
