"""Trip History view displaying recorded Blackbox sessions.
"""
import os
import subprocess
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLabel, QAbstractItemView
)
from PySide6.QtCore import Qt
from database.db import db
from blackbox.recovery import CrashRecovery


class TripHistoryView(QWidget):
    """Lists completed and active trips with access to folders and reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_trips()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header controls
        hdr_box = QHBoxLayout()
        hdr_box.setSpacing(10)

        lbl = QLabel("🚗 Histórico de Viagens (Caixa-Preta)")
        lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        hdr_box.addWidget(lbl)
        hdr_box.addStretch()

        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.clicked.connect(self.load_trips)
        hdr_box.addWidget(self.btn_refresh)

        self.btn_open_folder = QPushButton("📁 Abrir Pasta da Viagem")
        self.btn_open_folder.clicked.connect(self._open_selected_folder)
        hdr_box.addWidget(self.btn_open_folder)

        self.btn_recover = QPushButton("🛠️ Recuperar Incompletas")
        self.btn_recover.setObjectName("secondaryBtn")
        self.btn_recover.clicked.connect(self._check_recovery)
        hdr_box.addWidget(self.btn_recover)

        layout.addLayout(hdr_box)

        # Trips table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID Viagem", "Início", "Duração", "DTCs", "Eventos", "Desconexões", "Status", "Pasta Local"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_trips(self):
        trips = db.list_trips()
        self.table.setRowCount(len(trips))

        for row, t in enumerate(trips):
            dur_sec = t.get("duration_sec", 0)
            mins = int(dur_sec // 60)
            secs = int(dur_sec % 60)
            dur_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

            status = t.get("status", "FINALIZADA")
            status_icon = "🟢" if t.get("dtc_count", 0) == 0 else "⚠️"
            if status == "EM_ANDAMENTO":
                status_icon = "🔵 Gravando"

            self.table.setItem(row, 0, QTableWidgetItem(t.get("trip_id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(t.get("start_time", "")))
            self.table.setItem(row, 2, QTableWidgetItem(dur_str))
            self.table.setItem(row, 3, QTableWidgetItem(str(t.get("dtc_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(str(t.get("events_count", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(str(t.get("disconnect_count", 0))))
            self.table.setItem(row, 6, QTableWidgetItem(f"{status_icon} {status}"))
            self.table.setItem(row, 7, QTableWidgetItem(t.get("folder_path", "")))

    def _open_selected_folder(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma viagem na tabela.")
            return

        folder_item = self.table.item(curr_row, 7)
        if not folder_item:
            return

        folder_path = folder_item.text()
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir a pasta: {str(e)}")
        else:
            QMessageBox.warning(self, "Aviso", f"Pasta não encontrada:\n{folder_path}")

    def _check_recovery(self):
        incomplete = CrashRecovery.find_incomplete_trips()
        if not incomplete:
            QMessageBox.information(self, "Recuperação", "Nenhuma viagem incompleta encontrada. Todas as sessões anteriores foram finalizadas corretamente.")
            return

        count = 0
        for item in incomplete:
            folder = item.get("folder_path")
            if folder and CrashRecovery.recover_trip(folder):
                count += 1

        QMessageBox.information(self, "Recuperação Concluída", f"{count} viagem(ns) incompleta(s) recuperada(s) e consolidadas!")
        self.load_trips()
