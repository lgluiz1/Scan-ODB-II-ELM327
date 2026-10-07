"""Diagnostic Events View with filtering and access to 90s pre/post buffers.
"""
import os
import webbrowser
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLabel, QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from database.db import db


class EventsView(QWidget):
    """Lists diagnostic, suspicious, and communication events with access to event reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_events()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Filter bar
        hdr_box = QHBoxLayout()
        hdr_box.setSpacing(10)

        lbl = QLabel("🚨 Histórico de Eventos Capturados")
        lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        hdr_box.addWidget(lbl)

        lbl_filter = QLabel("Filtrar por tipo:")
        lbl_filter.setStyleSheet("color: #94a3b8; font-weight: 600; margin-left: 14px;")
        hdr_box.addWidget(lbl_filter)

        self.combo_filter = QComboBox()
        self.combo_filter.addItem("TODOS", "TODOS")
        self.combo_filter.addItem("🟥 DTC Confirmado", "DTC")
        self.combo_filter.addItem("🟨 Evento Suspeito", "SUSPEITO")
        self.combo_filter.addItem("🟦 Comunicação", "COMUNICACAO")
        self.combo_filter.currentIndexChanged.connect(self.load_events)
        hdr_box.addWidget(self.combo_filter)

        hdr_box.addStretch()

        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.clicked.connect(self.load_events)
        hdr_box.addWidget(self.btn_refresh)

        self.btn_open_report = QPushButton("🌐 Abrir Relatório do Evento")
        self.btn_open_report.clicked.connect(self._open_report)
        hdr_box.addWidget(self.btn_open_report)

        self.btn_open_folder = QPushButton("📁 Abrir Pasta")
        self.btn_open_folder.setObjectName("secondaryBtn")
        self.btn_open_folder.clicked.connect(self._open_folder)
        hdr_box.addWidget(self.btn_open_folder)

        layout.addLayout(hdr_box)

        # Events table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Data / Hora", "Tipo", "Código", "Título do Evento", "Viagem", "Pasta do Evento"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_events(self):
        filter_type = self.combo_filter.currentData()
        events = db.list_trip_events(event_type=filter_type)
        self.table.setRowCount(len(events))

        for row, ev in enumerate(events):
            t_type = ev.get("event_type", "")
            icon = "🟥" if t_type == "DTC" else ("🟨" if t_type == "SUSPEITO" else "🟦")

            self.table.setItem(row, 0, QTableWidgetItem(ev.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(f"{icon} {t_type}"))
            self.table.setItem(row, 2, QTableWidgetItem(ev.get("code", "")))
            self.table.setItem(row, 3, QTableWidgetItem(ev.get("title", "")))
            self.table.setItem(row, 4, QTableWidgetItem(ev.get("trip_id", "")))
            self.table.setItem(row, 5, QTableWidgetItem(ev.get("folder_path", "")))

    def _open_report(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Aviso", "Selecione um evento na tabela.")
            return

        folder_item = self.table.item(curr_row, 5)
        if not folder_item or not folder_item.text():
            QMessageBox.warning(self, "Aviso", "Pasta do evento não encontrada.")
            return

        report_path = os.path.join(folder_item.text(), "relatorio.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file:///{os.path.abspath(report_path).replace(os.sep, '/')}")
        else:
            QMessageBox.information(self, "Aviso", f"Relatório HTML ainda não gerado ou não encontrado em:\n{report_path}")

    def _open_folder(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Aviso", "Selecione um evento na tabela.")
            return

        folder_item = self.table.item(curr_row, 5)
        if folder_item and os.path.exists(folder_item.text()):
            os.startfile(folder_item.text())
        else:
            QMessageBox.warning(self, "Aviso", "Pasta do evento não encontrada.")
