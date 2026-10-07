"""Diagnostic history view showing past scan sessions from SQLite database.
"""
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLabel, QAbstractItemView
)
from PySide6.QtCore import Qt
from database.db import db


class HistoryView(QWidget):
    """View and manage past diagnostic sessions stored locally."""

    def __init__(self, on_load_session: Optional[Callable[[dict], None]] = None, parent=None):
        super().__init__(parent)
        self.on_load_session = on_load_session

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header controls
        header_bar = QHBoxLayout()
        header_bar.setSpacing(10)

        lbl = QLabel("📜 Histórico de Sessões de Diagnóstico")
        lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        header_bar.addWidget(lbl)
        header_bar.addStretch()

        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.clicked.connect(self.load_history)
        header_bar.addWidget(self.btn_refresh)

        self.btn_delete = QPushButton("🗑️ Excluir Selecionado")
        self.btn_delete.setObjectName("secondaryBtn")
        self.btn_delete.clicked.connect(self._delete_selected)
        header_bar.addWidget(self.btn_delete)

        layout.addLayout(header_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data / Hora", "Veículo", "Protocolo", "Tensão", "Qtd Códigos", "Códigos Encontrados"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.load_history()

    def load_history(self):
        sessions = db.list_sessions()
        self.table.setRowCount(len(sessions))

        for row, s in enumerate(sessions):
            all_codes = list(set(s.get("stored_codes", []) + s.get("pending_codes", []) + s.get("permanent_codes", [])))
            codes_str = ", ".join(all_codes) if all_codes else "Nenhum código"

            self.table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(s["created_at"]))
            self.table.setItem(row, 2, QTableWidgetItem(s.get("vehicle_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(s.get("protocol_name", "")))
            self.table.setItem(row, 4, QTableWidgetItem(s.get("battery_voltage", "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(len(all_codes))))
            self.table.setItem(row, 6, QTableWidgetItem(codes_str))

    def _delete_selected(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma sessão na tabela para excluir.")
            return

        session_id_item = self.table.item(curr_row, 0)
        if not session_id_item:
            return

        session_id = int(session_id_item.text())
        ans = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir a sessão #{session_id} do histórico?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            db.delete_session(session_id)
            self.load_history()
