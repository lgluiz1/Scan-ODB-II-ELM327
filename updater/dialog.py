"""Update notification and in-app downloader dialog for OBD Scanner.
"""
import os
import sys
import tempfile
import webbrowser
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextBrowser, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal

from app.config import APP_VERSION, APP_NAME
from updater.checker import check_for_updates, download_file, apply_update_and_restart
from utils.logger import tech_logger


class CheckUpdateWorker(QThread):
    """Background worker for querying GitHub releases without freezing the UI."""
    finished = Signal(object)  # dict with info or None

    def run(self):
        result = check_for_updates()
        self.finished.emit(result)


class DownloadWorker(QThread):
    """Background worker for downloading the executable binary with live progress."""
    progress = Signal(int, int)  # (received_bytes, total_bytes)
    finished = Signal(bool, str)  # (success, path_or_error)

    def __init__(self, download_url: str):
        super().__init__()
        self.download_url = download_url
        self.dest_path = os.path.join(tempfile.gettempdir(), "OBDScanner_update.exe")

    def run(self):
        def _cb(recv, total):
            self.progress.emit(recv, total)

        tech_logger.info(f"[UPDATER] Iniciando download de {self.download_url} para {self.dest_path}...")
        ok = download_file(self.download_url, self.dest_path, progress_callback=_cb)
        if ok and os.path.exists(self.dest_path):
            self.finished.emit(True, self.dest_path)
        else:
            self.finished.emit(False, "Falha no download da atualização.")


class UpdateDialog(QDialog):
    """
    Modern dark-themed update dialog displaying version notes, progress, and auto-restart.
    """

    def __init__(self, update_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_worker: Optional[DownloadWorker] = None

        self.setWindowTitle(f"Atualização do {APP_NAME}")
        self.setMinimumWidth(540)
        self.resize(560, 420)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 1. Header Banner
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        h_box = QHBoxLayout(hdr_frame)
        h_box.setContentsMargins(10, 6, 10, 6)
        h_box.setSpacing(12)

        lbl_icon = QLabel("🚀")
        lbl_icon.setStyleSheet("font-size: 28px; background: transparent;")
        h_box.addWidget(lbl_icon)

        v_t = QVBoxLayout()
        v_t.setSpacing(2)
        lbl_t = QLabel(f"Nova Versão Disponível: {self.update_info.get('remote_version', '')}")
        lbl_t.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8; background: transparent;")
        v_t.addWidget(lbl_t)

        curr_ver = self.update_info.get('current_version', f'v{APP_VERSION}')
        lbl_sub = QLabel(f"Sua versão atual: {curr_ver} • Uma atualização mais recente foi publicada no GitHub.")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        v_t.addWidget(lbl_sub)
        h_box.addLayout(v_t)

        layout.addWidget(hdr_frame)

        # 2. Release Notes View
        lbl_notes_title = QLabel("📝 Novidades e Melhorias desta Versão:")
        lbl_notes_title.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 12px;")
        layout.addWidget(lbl_notes_title)

        self.browser_notes = QTextBrowser()
        self.browser_notes.setOpenExternalLinks(True)
        self.browser_notes.setStyleSheet("""
            QTextBrowser {
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 10px;
                color: #e2e8f0;
                font-size: 12px;
            }
        """)
        raw_notes = self.update_info.get("release_notes", "").strip() or "Nenhuma nota de versão especificada."
        # Simple markdown to HTML conversion for bullet points
        html_notes = raw_notes.replace("\n", "<br>")
        self.browser_notes.setHtml(f"<div style='line-height: 1.5;'>{html_notes}</div>")
        layout.addWidget(self.browser_notes, stretch=1)

        # 3. Download Progress Bar (initially hidden)
        self.progress_container = QWidget()
        v_prog = QVBoxLayout(self.progress_container)
        v_prog.setContentsMargins(0, 0, 0, 0)
        v_prog.setSpacing(4)

        self.lbl_progress_status = QLabel("Baixando pacote de atualização...")
        self.lbl_progress_status.setStyleSheet("font-size: 11px; color: #38bdf8; font-weight: 600;")
        v_prog.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 4px;
            }
        """)
        v_prog.addWidget(self.progress_bar)

        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        # 4. Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_web = QPushButton("🌐 Abrir no GitHub")
        self.btn_web.setObjectName("secondaryBtn")
        self.btn_web.clicked.connect(self._open_web)
        btn_box.addWidget(self.btn_web)

        btn_box.addStretch()

        self.btn_cancel = QPushButton("Lembrar Mais Tarde")
        self.btn_cancel.setObjectName("secondaryBtn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_update = QPushButton("🚀 ATUALIZAR AGORA")
        self.btn_update.setObjectName("successBtn")
        self.btn_update.setStyleSheet("font-weight: 700; padding: 8px 18px;")
        self.btn_update.clicked.connect(self._start_download)
        btn_box.addWidget(self.btn_update)

        layout.addLayout(btn_box)

    def _open_web(self):
        url = self.update_info.get("html_url") or "https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases"
        webbrowser.open(url)

    def _start_download(self):
        dl_url = self.update_info.get("download_url")

        # If not packaged as frozen .exe, inform developer
        is_frozen = getattr(sys, "frozen", False)
        if not is_frozen:
            QMessageBox.information(
                self,
                "Modo Desenvolvimento",
                "Você está executando o aplicativo diretamente via Python.\n\n"
                "Para atualizar o código-fonte, use 'git pull'.\n"
                "O executável oficial será aberto na página do GitHub."
            )
            self._open_web()
            self.accept()
            return

        if not dl_url:
            QMessageBox.warning(
                self,
                "Download Manual",
                "O instalador automático não encontrou o executável anexado à release.\n"
                "A página do GitHub será aberta para download manual."
            )
            self._open_web()
            self.accept()
            return

        # Start download
        self.btn_update.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_web.setEnabled(False)
        self.progress_container.setVisible(True)

        self.download_worker = DownloadWorker(dl_url)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.start()

    def _on_download_progress(self, received: int, total: int):
        if total > 0:
            pct = int((received / total) * 100)
            self.progress_bar.setValue(pct)
            mb_recv = received / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.lbl_progress_status.setText(f"Baixando atualização... {mb_recv:.1f} MB de {mb_total:.1f} MB ({pct}%)")
        else:
            mb_recv = received / (1024 * 1024)
            self.lbl_progress_status.setText(f"Baixando atualização... {mb_recv:.1f} MB")

    def _on_download_finished(self, success: bool, path_or_error: str):
        if not success:
            self.progress_container.setVisible(False)
            self.btn_update.setEnabled(True)
            self.btn_cancel.setEnabled(True)
            self.btn_web.setEnabled(True)
            QMessageBox.critical(self, "Erro na Atualização", f"Não foi possível baixar o arquivo:\n{path_or_error}")
            return

        self.lbl_progress_status.setText("Download concluído! Aplicando nova versão e reiniciando...")
        self.progress_bar.setValue(100)

        # Apply update
        ok, msg = apply_update_and_restart(path_or_error)
        if ok:
            tech_logger.info("[UPDATER] Atualização aplicada. Encerrando aplicação para reinício...")
            QApplication.quit()
        else:
            QMessageBox.warning(self, "Aviso", msg)
            self.btn_update.setEnabled(True)
            self.btn_cancel.setEnabled(True)
