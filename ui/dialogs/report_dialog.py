"""Report preview and export dialog.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QPushButton, QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt


class ReportDialog(QDialog):
    """Modal dialog allowing preview and export of diagnostic report to HTML and TXT."""

    def __init__(self, html_content: str, txt_content: str, parent=None):
        super().__init__(parent)
        self.html_content = html_content
        self.txt_content = txt_content

        self.setWindowTitle("Relatório de Diagnóstico OBD2")
        self.resize(800, 650)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        lbl = QLabel("Visualização Prévia do Relatório de Diagnóstico")
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(lbl)

        # HTML Viewer
        self.viewer = QTextBrowser()
        self.viewer.setHtml(self.html_content)
        self.viewer.setOpenExternalLinks(True)
        layout.addWidget(self.viewer)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_export_html = QPushButton("🌐 Salvar Relatório (.html)")
        self.btn_export_html.clicked.connect(self._export_html)
        btn_layout.addWidget(self.btn_export_html)

        self.btn_export_txt = QPushButton("📄 Salvar Texto (.txt)")
        self.btn_export_txt.setObjectName("secondaryBtn")
        self.btn_export_txt.clicked.connect(self._export_txt)
        btn_layout.addWidget(self.btn_export_txt)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Fechar")
        self.btn_close.setObjectName("secondaryBtn")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _export_html(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório HTML",
            "diagnostico_renault_logan.html",
            "Arquivos HTML (*.html *.htm)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.html_content)
                QMessageBox.information(self, "Sucesso", f"Relatório HTML salvo em:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{str(e)}")

    def _export_txt(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório TXT",
            "diagnostico_renault_logan.txt",
            "Arquivos de Texto (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.txt_content)
                QMessageBox.information(self, "Sucesso", f"Relatório TXT salvo em:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{str(e)}")
