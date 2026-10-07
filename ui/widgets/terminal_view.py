"""Terminal view widget for live serial logging and diagnostics.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QCheckBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QTextCursor, QGuiApplication
from PySide6.QtCore import Qt, Signal
from utils.logger import tech_logger, LogEntry


class TerminalView(QWidget):
    """Live scrolling technical log terminal with copy and export functionality."""
    new_log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header bar
        header_bar = QHBoxLayout()
        header_bar.setSpacing(10)

        lbl_title = QLabel("📡 Registro Técnico de Comunicação Serial (TX/RX)")
        lbl_title.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        header_bar.addWidget(lbl_title)
        header_bar.addStretch()

        self.chk_autoscroll = QCheckBox("Rolar automaticamente")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.setStyleSheet("color: #94a3b8;")
        header_bar.addWidget(self.chk_autoscroll)

        self.btn_copy = QPushButton("📋 Copiar Log")
        self.btn_copy.setObjectName("secondaryBtn")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        header_bar.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Salvar (.txt)")
        self.btn_save.setObjectName("secondaryBtn")
        self.btn_save.clicked.connect(self._save_log_file)
        header_bar.addWidget(self.btn_save)

        self.btn_clear = QPushButton("🗑️ Limpar")
        self.btn_clear.setObjectName("secondaryBtn")
        self.btn_clear.clicked.connect(self._clear_log)
        header_bar.addWidget(self.btn_clear)

        layout.addLayout(header_bar)

        # Text Console
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setMaximumBlockCount(5000)
        layout.addWidget(self.text_edit)

        # Thread-safe signal to marshal log updates to main GUI thread
        self.new_log_signal.connect(self._append_log_text)

        # Register callback with tech_logger
        tech_logger.add_listener(self._on_new_log_entry)

    def _on_new_log_entry(self, entry: LogEntry):
        # Called from background threads: emit signal to cross thread boundary safely
        self.new_log_signal.emit(entry.formatted())

    def _append_log_text(self, text: str):
        # Executed exclusively on Qt main thread
        self.text_edit.appendPlainText(text)
        if self.chk_autoscroll.isChecked():
            self.text_edit.moveCursor(QTextCursor.End)

    def _copy_to_clipboard(self):
        text = self.text_edit.toPlainText()
        if not text:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copiado", "Log técnico copiado para a área de transferência!")

    def _save_log_file(self):
        text = self.text_edit.toPlainText()
        if not text:
            QMessageBox.information(self, "Aviso", "O log técnico está vazio.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Log Técnico",
            "elm327_communication_log.txt",
            "Arquivos de Texto (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                QMessageBox.information(self, "Salvo", f"Log salvo com sucesso em:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    def _clear_log(self):
        self.text_edit.clear()
        tech_logger.clear()
