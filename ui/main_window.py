"""Main application window for OBD Scanner with Integrated Blackbox (Modo Viagem).
"""
from typing import List, Optional
import os
import time

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTabWidget, QScrollArea, QFrame,
    QMessageBox, QStatusBar, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer

from app.config import (
    APP_NAME, APP_VERSION, VEHICLE_PROFILE_DEFAULT,
    SUPPORTED_BAUDRATES, SAFETY_WARNING
)
from elm327.connection import ELM327Connection, SerialPortInfo
from elm327.mock_adapter import MockELM327Connection
from dtc.reader import DTCReader, DTCItem
from dtc.advisor import DiagnosticAdvisor
from database.db import db
from reports.generator import ReportGenerator
from utils.logger import tech_logger
from updater.dialog import CheckUpdateWorker, UpdateDialog
from app.i18n import tr, get_current_language

from blackbox.config import BlackboxConfig
from blackbox.trip_manager import TripManager
from blackbox.monitor import TripMonitor
from blackbox.recovery import CrashRecovery

from ui.widgets.status_badge import StatusBadge
from ui.widgets.dtc_card import DTCCard
from ui.widgets.terminal_view import TerminalView
from ui.widgets.history_view import HistoryView
from ui.widgets.blackbox_view import BlackboxView
from ui.widgets.trip_history_view import TripHistoryView
from ui.widgets.events_view import EventsView
from ui.widgets.patterns_view import PatternsView
from ui.widgets.lambda_view import LambdaView
from ui.dialogs.report_dialog import ReportDialog


class ConnectWorker(QThread):
    """Background worker for non-blocking serial connection and ECU initialization."""
    finished = Signal(bool, str, object)

    def __init__(self, port: str, baudrate: int, is_mock: bool):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.is_mock = is_mock

    def run(self):
        try:
            if self.is_mock:
                conn = MockELM327Connection(port="SIMULAÇÃO (MOCK)", baudrate=self.baudrate)
            else:
                conn = ELM327Connection(port=self.port, baudrate=self.baudrate)

            # 1. Connect serial
            ok, msg = conn.connect()
            if not ok:
                self.finished.emit(False, msg, None)
                return

            # 2. Init ELM327
            ok_init, msg_init = conn.initialize_elm()
            if not ok_init:
                conn.disconnect()
                self.finished.emit(False, f"Falha na inicialização do ELM327: {msg_init}", None)
                return

            # 3. Test ECU communication
            ok_ecu, msg_ecu = conn.test_ecu_communication()
            self.finished.emit(True, msg_ecu, conn)

        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {str(e)}", None)


class ReadDTCWorker(QThread):
    """Background worker for querying Diagnostic Trouble Codes without freezing UI."""
    finished = Signal(bool, str, list)

    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def run(self):
        try:
            reader = DTCReader(self.connection)
            items, msg = reader.read_all_dtcs()
            self.finished.emit(True, msg, items)
        except Exception as e:
            self.finished.emit(False, f"Erro ao ler códigos: {str(e)}", [])


class MainWindow(QMainWindow):
    """Primary application window for OBD Scanner with Caixa-Preta capability."""

    def __init__(self):
        super().__init__()
        self.conn: Optional[ELM327Connection] = None
        self.current_dtcs: List[DTCItem] = []
        self.worker: Optional[QThread] = None

        # Blackbox subsystem
        self.trip_manager = TripManager()
        self.trip_monitor: Optional[TripMonitor] = None

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — Universal Automotive Diagnostic Tool")
        self.setMinimumSize(920, 560)
        self.resize(1120, 720)

        self._update_worker = None

        self._init_ui()
        self._refresh_ports()
        self._check_for_interrupted_trips()

        # Non-blocking automatic check for updates on startup (after 3s)
        QTimer.singleShot(3000, lambda: self._check_for_updates(manual=False))

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # 1. Top Header & Connection Controls (Compact & Unified)
        main_layout.addWidget(self._create_top_header())

        # 2. Status Badges & Quick Action Controls (Compact & Unified)
        main_layout.addWidget(self._create_status_actions_bar())

        # 3. Main Content Tabs
        self.tabs = QTabWidget()
        self.tab_dtc = self._create_dtc_tab()
        self.tab_blackbox = BlackboxView(
            on_start_trip=self._start_blackbox_trip,
            on_pause_trip=self._pause_blackbox_trip,
            on_stop_trip=self._stop_blackbox_trip
        )
        self.tab_lambda = LambdaView()
        self.tab_trip_history = TripHistoryView()
        self.tab_events = EventsView()
        self.tab_patterns = PatternsView()
        self.tab_terminal = TerminalView()
        self.tab_history = HistoryView()

        self.tabs.addTab(self.tab_dtc, tr("tab_dtc", "🔍 Leitor de Falhas (DTC)"))
        self.tabs.addTab(self.tab_lambda, tr("tab_lambda", "📈 Osciloscópio Lambda (O2)"))
        self.tabs.addTab(self.tab_blackbox, tr("tab_blackbox", "🚗 Telemetria & Viagem"))
        self.tabs.addTab(self.tab_trip_history, tr("tab_trips", "🗺️ Viagens Salvas"))
        self.tabs.addTab(self.tab_events, tr("tab_events", "⚠️ Eventos Críticos"))
        self.tabs.addTab(self.tab_patterns, tr("tab_patterns", "📊 Padrões Operacionais"))
        self.tabs.addTab(self.tab_terminal, tr("tab_terminal", "💻 Terminal OBD2"))
        self.tabs.addTab(self.tab_history, tr("tab_history", "📁 Histórico DTC"))
        main_layout.addWidget(self.tabs, stretch=1)

        # 4. Status Bar & Footer
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Developer & Creator credit badge in footer
        self.lbl_developer_credit = QLabel(tr("developer_credit", "👨‍💻 Desenvolvido e criado por Luiz Gustavo"))
        self.lbl_developer_credit.setStyleSheet("""
            color: #38bdf8;
            font-weight: 700;
            font-size: 11px;
            padding: 2px 14px;
            background-color: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            margin-right: 6px;
        """)
        self.status_bar.addPermanentWidget(self.lbl_developer_credit)

        # Check updates button in status bar
        self.btn_check_update = QPushButton("🔄 Atualizações")
        self.btn_check_update.setObjectName("secondaryBtn")
        self.btn_check_update.setToolTip("Verificar se há novas versões disponíveis no GitHub")
        self.btn_check_update.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 2px 8px;
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #94a3b8;
                font-weight: 600;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #38bdf8;
            }
        """)
        self.btn_check_update.clicked.connect(lambda: self._check_for_updates(manual=True))
        self.status_bar.addPermanentWidget(self.btn_check_update)

        self.status_bar.showMessage("Pronto para conectar ao adaptador ELM327.")

    def _check_for_updates(self, manual: bool = False):
        """Checks GitHub Releases for new versions and shows UpdateDialog if available."""
        if manual:
            self.status_bar.showMessage("Verificando se há atualizações no GitHub...")

        def _on_finished(info):
            if manual:
                self.status_bar.showMessage("Verificação de atualizações concluída.", 4000)

            if not info:
                if manual:
                    QMessageBox.information(
                        self,
                        "Verificar Atualizações",
                        f"Não foi possível consultar os servidores do GitHub ou nenhuma release foi publicada ainda.\n\n"
                        f"Versão atual do aplicativo: v{APP_VERSION}."
                    )
                return

            if info.get("has_update"):
                dlg = UpdateDialog(info, self)
                dlg.exec()
            elif manual:
                QMessageBox.information(
                    self,
                    "Atualizado!",
                    f"🎉 Parabéns!\nVocê já está utilizando a versão mais recente do OBD Scanner (v{APP_VERSION})."
                )

        worker = CheckUpdateWorker(self)
        worker.finished.connect(_on_finished)
        self._update_worker = worker
        worker.start()

    def _create_top_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("topHeaderFrame")
        frame.setStyleSheet("""
            QFrame#topHeaderFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #131c2e, stop:1 #0f172a);
                border: 1px solid #233149;
                border-radius: 8px;
            }
        """)
        h_layout = QHBoxLayout(frame)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(10)

        # App Title & Vehicle Profile
        v_title = QVBoxLayout()
        v_title.setSpacing(1)
        lbl_app = QLabel(tr("app_title", "⚡ ODBScan II"))
        lbl_app.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; background: transparent;")
        v_title.addWidget(lbl_app)

        lbl_desc = QLabel(tr("app_desc", "Scanner Automotivo Universal (SAE J1979 / CAN)"))
        lbl_desc.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        v_title.addWidget(lbl_desc)
        h_layout.addLayout(v_title)

        h_layout.addSpacing(10)

        # Port Selector
        lbl_port = QLabel(tr("port", "Porta:"))
        lbl_port.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 11px; background: transparent;")
        h_layout.addWidget(lbl_port)

        self.combo_ports = QComboBox()
        self.combo_ports.setMinimumWidth(160)
        h_layout.addWidget(self.combo_ports)

        self.btn_refresh_ports = QPushButton("🔄")
        self.btn_refresh_ports.setToolTip("Atualizar portas seriais")
        self.btn_refresh_ports.setObjectName("secondaryBtn")
        self.btn_refresh_ports.setStyleSheet("padding: 4px 8px; font-size: 12px;")
        self.btn_refresh_ports.clicked.connect(self._refresh_ports)
        h_layout.addWidget(self.btn_refresh_ports)

        # Baudrate
        lbl_baud = QLabel(tr("baudrate", "Baud:"))
        lbl_baud.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 11px; background: transparent;")
        h_layout.addWidget(lbl_baud)

        self.combo_baud = QComboBox()
        for b in SUPPORTED_BAUDRATES:
            self.combo_baud.addItem(str(b), b)
        self.combo_baud.setCurrentText("38400")
        self.combo_baud.setMinimumWidth(75)
        h_layout.addWidget(self.combo_baud)

        # Connect / Disconnect Buttons
        self.btn_connect = QPushButton(tr("connect", "🔌 CONECTAR"))
        self.btn_connect.setObjectName("successBtn")
        self.btn_connect.setStyleSheet("font-weight: 700; padding: 5px 12px; font-size: 11px;")
        self.btn_connect.clicked.connect(self._handle_connect)
        h_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton(tr("disconnect", "⏹️ DESCONECTAR"))
        self.btn_disconnect.setObjectName("secondaryBtn")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.setStyleSheet("padding: 5px 10px; font-size: 11px;")
        self.btn_disconnect.clicked.connect(self._handle_disconnect)
        h_layout.addWidget(self.btn_disconnect)

        h_layout.addStretch()

        # Read-Only Safety Mode Badge
        lbl_safety = QLabel("🛡️ SOMENTE LEITURA")
        lbl_safety.setStyleSheet("""
            background-color: #172554;
            color: #93c5fd;
            border: 1px solid #1e40af;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 10px;
        """)
        h_layout.addWidget(lbl_safety)

        return frame

    def _create_status_actions_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("statusActionsFrame")
        frame.setStyleSheet("""
            QFrame#statusActionsFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)

        # 3 Status Badges
        self.badge_elm = StatusBadge("🔌", "Adaptador ELM327", "Desconectado")
        layout.addWidget(self.badge_elm)

        self.badge_ecu = StatusBadge("🚗", "Comunicação ECU", "Não conectada")
        layout.addWidget(self.badge_ecu)

        self.badge_volt = StatusBadge("⚡", "Tensão Bateria", "-- V")
        layout.addWidget(self.badge_volt)

        layout.addSpacing(10)

        # Action Buttons
        self.btn_read_dtc = QPushButton("🔍 LER CÓDIGOS")
        self.btn_read_dtc.setEnabled(False)
        self.btn_read_dtc.setStyleSheet("padding: 6px 14px; font-size: 11px; font-weight: 700;")
        self.btn_read_dtc.clicked.connect(self._handle_read_dtcs)
        layout.addWidget(self.btn_read_dtc)

        self.btn_clear_dtc = QPushButton("🗑️ LIMPAR CÓDIGOS")
        self.btn_clear_dtc.setObjectName("dangerBtn")
        self.btn_clear_dtc.setEnabled(False)
        self.btn_clear_dtc.setStyleSheet("""
            QPushButton {
                background-color: #7f1d1d;
                border: 1px solid #b91c1c;
                color: #fecaca;
                font-weight: 700;
                font-size: 11px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #991b1b;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #64748b;
            }
        """)
        self.btn_clear_dtc.clicked.connect(self._handle_clear_dtcs)
        layout.addWidget(self.btn_clear_dtc)

        self.btn_export_report = QPushButton("📑 EXPORTAR")
        self.btn_export_report.setObjectName("secondaryBtn")
        self.btn_export_report.setEnabled(False)
        self.btn_export_report.setStyleSheet("padding: 6px 12px; font-size: 11px;")
        self.btn_export_report.clicked.connect(self._handle_export_report)
        layout.addWidget(self.btn_export_report)

        # Reference retained for compatibility
        self.btn_goto_blackbox = QPushButton("🚗 MODO VIAGEM")
        self.btn_goto_blackbox.setObjectName("secondaryBtn")
        self.btn_goto_blackbox.clicked.connect(lambda: self.tabs.setCurrentWidget(self.tab_blackbox))

        layout.addStretch()

        return frame

    def _create_dtc_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Scroll Area for DTC Cards & Correlations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.dtc_cards_container = QWidget()
        self.dtc_cards_layout = QVBoxLayout(self.dtc_cards_container)
        self.dtc_cards_layout.setContentsMargins(4, 4, 4, 4)
        self.dtc_cards_layout.setSpacing(10)

        # Correlation Banner Container (Placed INSIDE scroll area, neatly styled)
        self.corr_container = QFrame()
        self.corr_container.setObjectName("corrContainer")
        self.corr_container.setVisible(False)
        self.corr_container.setStyleSheet("""
            QFrame#corrContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e1b4b, stop:1 #131238);
                border: 1px solid #4338ca;
                border-radius: 8px;
            }
        """)
        self.corr_layout = QVBoxLayout(self.corr_container)
        self.corr_layout.setContentsMargins(12, 12, 12, 12)
        self.corr_layout.setSpacing(8)
        self.dtc_cards_layout.addWidget(self.corr_container)

        # Initial Empty State Card
        self.lbl_empty_state = QLabel(
            "Nenhum diagnóstico realizado ainda.\n"
            "Conecte o adaptador ELM327 USB e clique em 'LER CÓDIGOS DE FALHA'."
        )
        self.lbl_empty_state.setAlignment(Qt.AlignCenter)
        self.lbl_empty_state.setStyleSheet("""
            color: #64748b;
            font-size: 14px;
            padding: 50px;
            border: 2px dashed #1e293b;
            border-radius: 8px;
        """)
        self.dtc_cards_layout.addWidget(self.lbl_empty_state)
        self.dtc_cards_layout.addStretch()

        scroll.setWidget(self.dtc_cards_container)
        layout.addWidget(scroll, stretch=1)

        return widget

    def _refresh_ports(self):
        self.combo_ports.clear()
        ports = ELM327Connection.list_available_ports()

        for p in ports:
            self.combo_ports.addItem(f"🔌 {p.display_name()}", p.port)

        self.combo_ports.addItem("🧪 MODO SIMULAÇÃO (MOCK) - Teste Virtual", "MOCK")

        if ports:
            self.status_bar.showMessage(f"{len(ports)} porta(s) serial(is) detectada(s).")
        else:
            self.status_bar.showMessage("Nenhuma porta serial física encontrada. Você pode testar no 'Modo Simulação'.")

    def _handle_connect(self):
        port_data = self.combo_ports.currentData()
        if not port_data:
            QMessageBox.warning(self, "Aviso", "Selecione uma porta serial válida.")
            return

        baudrate = self.combo_baud.currentData()
        is_mock = (port_data == "MOCK")

        self.btn_connect.setEnabled(False)
        self.combo_ports.setEnabled(False)
        self.combo_baud.setEnabled(False)
        self.btn_refresh_ports.setEnabled(False)
        self.badge_elm.set_state("connecting", "Conectando ao adaptador...")
        self.badge_ecu.set_state("connecting", "Aguardando resposta...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.status_bar.showMessage("Conectando e inicializando adaptador ELM327...")

        self.worker = ConnectWorker(port=port_data, baudrate=baudrate, is_mock=is_mock)
        self.worker.finished.connect(self._on_connect_finished)
        self.worker.start()

    def _on_connect_finished(self, success: bool, message: str, conn):
        self.progress_bar.setVisible(False)

        if not success or not conn:
            self.badge_elm.set_state("error", "Falha de conexão")
            self.badge_ecu.set_state("disconnected", "Não conectada")
            self.btn_connect.setEnabled(True)
            self.combo_ports.setEnabled(True)
            self.combo_baud.setEnabled(True)
            self.btn_refresh_ports.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_read_dtc.setEnabled(False)
            QMessageBox.critical(self, "Erro de Conexão", message)
            self.status_bar.showMessage("Erro ao conectar.")
            return

        self.conn = conn
        self.btn_disconnect.setEnabled(True)
        self.btn_read_dtc.setEnabled(True)
        self.btn_clear_dtc.setEnabled(True)
        self.tab_lambda.set_connection(self.conn)

        self.badge_elm.set_state("connected", self.conn.elm_version)
        self.badge_volt.set_state("connected" if self.conn.battery_voltage != "0.0V" else "disconnected", self.conn.battery_voltage)

        if self.conn.ecu_connected:
            self.badge_ecu.set_state("connected", self.conn.protocol_name)
            self.status_bar.showMessage("Conectado com sucesso ao ELM327 e ECU!")
        else:
            self.badge_ecu.set_state("error", "Sem resposta da ECU (Chave ligada?)")
            self.status_bar.showMessage("Adaptador pronto, mas a ECU não respondeu. Verifique se a ignição está em ON.")
            QMessageBox.warning(
                self,
                "Aviso de Comunicação com a ECU",
                "O adaptador ELM327 foi detectado e inicializado com sucesso!\n\n"
                "Porém, a ECU do veículo não respondeu ao comando de teste (0100).\n\n"
                "Verifique se:\n"
                "1. A chave de ignição do Logan está na posição LIGADA (painel aceso).\n"
                "2. O conector OBD2 está firmemente encaixado na tomada do carro.\n\n"
                "Você ainda pode tentar clicar em 'LER CÓDIGOS DE FALHA'."
            )

    def _handle_disconnect(self):
        if self.trip_monitor and self.trip_monitor.isRunning():
            self._stop_blackbox_trip()

        self.tab_lambda.stop_monitoring()
        self.tab_lambda.set_connection(None)

        if self.conn:
            self.conn.disconnect()
            self.conn = None

        self.badge_elm.set_state("disconnected", "Desconectado")
        self.badge_ecu.set_state("disconnected", "Não conectada")
        self.badge_volt.set_state("disconnected", "-- V")

        self.btn_connect.setEnabled(True)
        self.combo_ports.setEnabled(True)
        self.combo_baud.setEnabled(True)
        self.btn_refresh_ports.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_read_dtc.setEnabled(False)
        self.btn_clear_dtc.setEnabled(False)
        self.status_bar.showMessage("Desconectado.")

    def _handle_clear_dtcs(self):
        """Sends OBD2 Mode 04 ('04') to erase trouble codes with safety confirmation."""
        if not self.conn or not self.conn.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao adaptador antes de limpar códigos.")
            return

        # Double safety confirmation dialog
        ans = QMessageBox.question(
            self,
            "⚠️ Confirmar Limpeza da ECU (Mode 04)",
            "ATENÇÃO: Você está prestes a enviar o comando de limpeza (Mode 04) para a ECU!\n\n"
            "O comando irá APAGAR:\n"
            "• Todos os códigos de falha armazenados e pendentes (Luz da Injeção).\n"
            "• Dados congelados da falha (Freeze Frames).\n"
            "• Mapas de auto-adaptação de combustível (STFT e LTFT).\n"
            "• Status dos monitores de prontidão de emissões (Readiness).\n\n"
            "REQUISITOS OBRIGATÓRIOS DO VEÍCULO:\n"
            "1. Chave de ignição na posição LIGADA (painel aceso).\n"
            "2. Motor DESLIGADO (não execute com o motor funcionando).\n\n"
            "Uma cópia de segurança dos códigos atuais já foi salva no histórico.\n\n"
            "Deseja realmente apagar todos os erros da ECU agora?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if ans != QMessageBox.Yes:
            return

        self.btn_clear_dtc.setEnabled(False)
        self.btn_read_dtc.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_bar.showMessage("Enviando comando OBD2 Mode 04 à ECU para apagar os códigos...")

        reader = DTCReader(self.conn)
        success, msg = reader.clear_all_dtcs()

        self.progress_bar.setVisible(False)
        self.btn_clear_dtc.setEnabled(True)
        self.btn_read_dtc.setEnabled(True)

        if success:
            self.status_bar.showMessage("Códigos apagados na ECU com sucesso! Revalidando leitura...")
            QMessageBox.information(
                self,
                "Sucesso na Limpeza",
                "O comando de limpeza (Mode 04) foi aceito com sucesso pela ECU!\n\n"
                "A memória de códigos de falha e os dados congelados foram reinicializados.\n\n"
                "O scanner fará uma releitura automática agora para confirmar se os erros foram totalmente removidos."
            )
            # Automatic re-read to verify that codes are cleared
            self._handle_read_dtcs()
        else:
            QMessageBox.critical(
                self,
                "Falha na Limpeza",
                f"A ECU não confirmou o comando de limpeza:\n\n{msg}\n\n"
                "Verifique se o motor está realmente desligado e a ignição ligada."
            )
            self.status_bar.showMessage("Falha ao apagar códigos na ECU.")

    def _handle_read_dtcs(self):
        if not self.conn or not self.conn.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao adaptador antes de ler códigos.")
            return

        self.btn_read_dtc.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_bar.showMessage("Lendo códigos de falha (Modos 03, 07, 0A)...")

        self.worker = ReadDTCWorker(self.conn)
        self.worker.finished.connect(self._on_read_dtcs_finished)
        self.worker.start()

    def _on_read_dtcs_finished(self, success: bool, message: str, items: List[DTCItem]):
        self.progress_bar.setVisible(False)
        self.btn_read_dtc.setEnabled(True)
        self.status_bar.showMessage(message)

        if not success:
            QMessageBox.critical(self, "Erro na Leitura", message)
            return

        self.current_dtcs = items
        self.btn_export_report.setEnabled(True)

        # Clear existing cards
        while self.dtc_cards_layout.count():
            child = self.dtc_cards_layout.takeAt(0)
            if child.widget() and child.widget() != self.corr_container:
                child.widget().deleteLater()

        # Re-add corr_container at the top
        self.dtc_cards_layout.addWidget(self.corr_container)

        # Check for correlations
        codes_list = [i.code for i in items]
        correlations = DiagnosticAdvisor.analyze_correlations(codes_list)

        # Clear inside correlation container
        while self.corr_layout.count():
            child = self.corr_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if correlations:
            self.corr_container.setVisible(True)
            lbl_corr_hdr = QLabel("🧠 CORRELAÇÃO DE FALHAS ENCONTRADAS")
            lbl_corr_hdr.setStyleSheet("color: #a5b4fc; font-weight: 800; font-size: 14px; margin-bottom: 4px;")
            self.corr_layout.addWidget(lbl_corr_hdr)

            for corr in correlations:
                c_box = QFrame()
                c_box.setObjectName("corrItem")
                c_box.setStyleSheet("""
                    QFrame#corrItem {
                        background-color: #2e1065;
                        border: 1px solid #7c3aed;
                        border-radius: 6px;
                        padding: 10px;
                        margin-top: 4px;
                    }
                """)
                v = QVBoxLayout(c_box)
                v.setContentsMargins(8, 8, 8, 8)
                v.setSpacing(4)

                t = QLabel(corr["title"])
                t.setStyleSheet("font-weight: 700; color: #fb7185; font-size: 13px;")
                v.addWidget(t)

                s = QLabel(corr["summary"])
                s.setWordWrap(True)
                s.setStyleSheet("color: #f1f5f9; font-size: 12px;")
                v.addWidget(s)

                for check in corr.get("checklist", []):
                    ch_lbl = QLabel(f"• {check}")
                    ch_lbl.setWordWrap(True)
                    ch_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; margin-left: 8px;")
                    v.addWidget(ch_lbl)

                self.corr_layout.addWidget(c_box)
        else:
            self.corr_container.setVisible(False)

        # Populate DTC Cards
        if not items:
            lbl_none = QLabel("✔️ Nenhum código de falha ativo ou pendente registrado na ECU!")
            lbl_none.setAlignment(Qt.AlignCenter)
            lbl_none.setStyleSheet("""
                color: #4ade80;
                font-weight: 600;
                font-size: 15px;
                padding: 40px;
                background-color: #064e3b;
                border: 1px solid #059669;
                border-radius: 8px;
            """)
            self.dtc_cards_layout.addWidget(lbl_none)
        else:
            for item in items:
                card = DTCCard(item)
                self.dtc_cards_layout.addWidget(card)

        self.dtc_cards_layout.addStretch()
        self._auto_save_session(items, correlations)

    def _auto_save_session(self, items: List[DTCItem], correlations):
        if not self.conn:
            return

        stored = [i.code for i in items if "Confirmado" in i.status]
        pending = [i.code for i in items if "Pendente" in i.status]
        permanent = [i.code for i in items if "Permanente" in i.status]
        notes = "\n".join([c["summary"] for c in correlations])

        db.save_session(
            vehicle_name=VEHICLE_PROFILE_DEFAULT,
            port=self.conn.port,
            baudrate=self.conn.baudrate,
            elm_version=self.conn.elm_version,
            protocol_name=self.conn.protocol_name,
            battery_voltage=self.conn.battery_voltage,
            stored_codes=stored,
            pending_codes=pending,
            permanent_codes=permanent,
            advisor_notes=notes,
            raw_log=tech_logger.get_full_log()
        )
        self.tab_history.load_history()

    def _handle_export_report(self):
        if not self.conn:
            return

        correlations = DiagnosticAdvisor.analyze_correlations([i.code for i in self.current_dtcs])
        raw_log = tech_logger.get_full_log()

        html = ReportGenerator.generate_html(
            vehicle_name=VEHICLE_PROFILE_DEFAULT,
            port=self.conn.port,
            elm_version=self.conn.elm_version,
            protocol=self.conn.protocol_name,
            voltage=self.conn.battery_voltage,
            dtc_items=self.current_dtcs,
            correlations=correlations,
            raw_log=raw_log
        )

        txt = ReportGenerator.generate_txt(
            vehicle_name=VEHICLE_PROFILE_DEFAULT,
            port=self.conn.port,
            elm_version=self.conn.elm_version,
            protocol=self.conn.protocol_name,
            voltage=self.conn.battery_voltage,
            dtc_items=self.current_dtcs,
            correlations=correlations,
            raw_log=raw_log
        )

        dlg = ReportDialog(html, txt, self)
        dlg.exec()

    # =========================================================================
    # BLACKBOX (MODO VIAGEM) METHODS
    # =========================================================================
    def _start_blackbox_trip(self):
        """Starts continuous Blackbox trip recording."""
        if not self.conn or not self.conn.is_connected:
            QMessageBox.warning(
                self,
                "Conexão Necessária",
                "Conecte-se ao adaptador ELM327 USB antes de iniciar o Modo Viagem."
            )
            return

        # Start trip session
        trip_meta = self.trip_manager.start_trip(
            port=self.conn.port,
            elm_version=self.conn.elm_version,
            protocol_name=self.conn.protocol_name,
            supported_pids=[]
        )
        db.save_trip(trip_meta)

        # Launch background acquisition thread
        self.trip_monitor = TripMonitor(
            connection=self.conn,
            trip_manager=self.trip_manager
        )
        self.trip_monitor.sample_recorded.connect(self.tab_blackbox.update_telemetry)
        self.trip_monitor.status_updated.connect(self.tab_blackbox.update_status)
        self.trip_monitor.event_detected.connect(self._on_blackbox_event_detected)
        self.trip_monitor.start()

        self.tab_blackbox.set_trip_started(trip_meta.trip_id)
        self.tabs.setCurrentWidget(self.tab_blackbox)
        self.status_bar.showMessage(f"Modo Viagem ativo: Gravando continuamente em {trip_meta.folder_path}")

    def _pause_blackbox_trip(self, is_paused: bool):
        if self.trip_monitor:
            self.trip_monitor.pause_monitoring(is_paused)
            if is_paused:
                self.status_bar.showMessage("Modo Viagem PAUSADO.")
            else:
                self.status_bar.showMessage("Modo Viagem RETOMADO.")

    def _stop_blackbox_trip(self):
        if self.trip_monitor and self.trip_monitor.isRunning():
            self.trip_monitor.stop_monitoring()
            self.trip_monitor = None

        trip_meta = self.trip_manager.stop_trip()
        if trip_meta:
            db.save_trip(trip_meta)

        self.tab_blackbox.set_trip_stopped()
        self.tab_trip_history.load_trips()
        self.tab_events.load_events()
        self.status_bar.showMessage("Viagem finalizada com sucesso.")

        if trip_meta:
            dur_mins = trip_meta.duration_sec / 60.0
            QMessageBox.information(
                self,
                "Resumo da Viagem",
                f"Viagem Finalizada!\n\n"
                f"• ID: {trip_meta.trip_id}\n"
                f"• Duração: {dur_mins:.1f} minutos\n"
                f"• DTCs Detectados: {trip_meta.dtc_count}\n"
                f"• Total de Eventos: {trip_meta.events_count}\n"
                f"• Desconexões: {trip_meta.disconnect_count}\n\n"
                f"Todos os dados foram salvos com segurança em:\n{trip_meta.folder_path}"
            )

    def _on_blackbox_event_detected(self, event):
        self.tab_blackbox.display_event(event)
        trip_id = self.trip_manager.current_trip.trip_id if self.trip_manager.current_trip else ""
        db.save_trip_event(event, trip_id)
        self.tab_events.load_events()

    def _check_for_interrupted_trips(self):
        """Prompt to recover unfinished trips after an unexpected shutdown."""
        incomplete = CrashRecovery.find_incomplete_trips()
        if incomplete:
            ans = QMessageBox.question(
                self,
                "Viagem Incompleta Detectada",
                f"Foi detectada uma viagem anterior não finalizada:\n\n"
                f"ID: {incomplete[0].get('trip_id')}\n"
                f"Data: {incomplete[0].get('start_time')}\n\n"
                f"Deseja recuperar e consolidar os dados já gravados desta viagem?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans == QMessageBox.Yes:
                for item in incomplete:
                    folder = item.get("folder_path")
                    if folder:
                        CrashRecovery.recover_trip(folder)
                self.tab_trip_history.load_trips()
