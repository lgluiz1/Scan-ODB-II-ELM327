"""Modern Dark Theme stylesheet and color tokens for OBD Scanner.
"""

DARK_THEME_QSS = """
/* Global Window & Base */
QMainWindow, QDialog {
    background-color: #0b1120;
    color: #f1f5f9;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: transparent;
    color: #e2e8f0;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0b1120;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #0b1120;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 25px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 7px 14px;
    margin-right: 3px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid transparent;
}

QTabBar::tab:selected {
    background-color: #0f172a;
    color: #38bdf8;
    border: 1px solid #334155;
    border-bottom: 1px solid #0f172a;
}

QTabBar::tab:hover:!selected {
    background-color: #273549;
    color: #cbd5e1;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #131c2e;
    border: 1px solid #233149;
    border-radius: 10px;
    margin-top: 18px;
    padding: 16px;
    font-weight: bold;
    font-size: 13px;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #38bdf8;
}

/* Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
    border: 1px solid #60a5fa;
}

QPushButton:pressed {
    background: #1e40af;
}

QPushButton:disabled {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #64748b;
}

/* Secondary Button Style */
QPushButton#secondaryBtn {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
}
QPushButton#secondaryBtn:hover {
    background-color: #334155;
    border: 1px solid #475569;
    color: #ffffff;
}

/* Danger Button Style */
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
    border: 1px solid #ef4444;
}
QPushButton#dangerBtn:hover {
    background: #ef4444;
}

/* Success Button Style */
QPushButton#successBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16a34a, stop:1 #15803d);
    border: 1px solid #22c55e;
}
QPushButton#successBtn:hover {
    background: #22c55e;
}

/* Combo Boxes */
QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f1f5f9;
    font-size: 13px;
    min-height: 24px;
}

QComboBox:hover {
    border: 1px solid #38bdf8;
}

QComboBox:focus {
    border: 1px solid #38bdf8;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #334155;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #1e293b;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    color: #f1f5f9;
    padding: 4px;
}

/* Line Edit */
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f5f9;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #38bdf8;
}

/* Tables */
QTableWidget {
    background-color: #131c2e;
    border: 1px solid #233149;
    border-radius: 8px;
    gridline-color: #1e293b;
    color: #f1f5f9;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 8px;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 8px;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid #334155;
}

/* Plain Text Edit / Log Terminal */
QPlainTextEdit {
    background-color: #020617;
    border: 1px solid #1e293b;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    color: #a5f3fc;
    padding: 8px;
}

/* Labels */
QLabel {
    color: #e2e8f0;
}
"""
