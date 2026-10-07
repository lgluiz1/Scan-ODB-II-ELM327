"""Card widget for displaying a single OBD2 DTC with neutral diagnostic guidance.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PySide6.QtCore import Qt
from dtc.reader import DTCItem


class DTCCard(QFrame):
    """Visual card displaying DTC code, status, description, and neutral checklist."""

    def __init__(self, item: DTCItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("dtcCard")
        self.setStyleSheet("""
            QFrame#dtcCard {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Header row
        header = QHBoxLayout()
        header.setSpacing(10)

        # Code Badge
        code_lbl = QLabel(item.code)
        code_lbl.setStyleSheet("""
            background-color: #dc2626;
            color: #ffffff;
            font-weight: 800;
            font-size: 15px;
            padding: 4px 10px;
            border-radius: 6px;
            letter-spacing: 0.8px;
        """)
        header.addWidget(code_lbl)

        # Status Pill
        status_color = "#38bdf8"
        if "Confirmado" in item.status:
            status_color = "#f87171"
        elif "Pendente" in item.status:
            status_color = "#fbbf24"

        status_lbl = QLabel(item.status)
        status_lbl.setStyleSheet(f"""
            background-color: #1e293b;
            color: {status_color};
            border: 1px solid #334155;
            font-size: 12px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 12px;
        """)
        header.addWidget(status_lbl)

        # System
        sys_lbl = QLabel(f"Sistema: {item.meta.system}")
        sys_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        header.addWidget(sys_lbl)

        header.addStretch()
        layout.addLayout(header)

        # 2. Description
        desc_lbl = QLabel(item.meta.description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #f1f5f9;")
        layout.addWidget(desc_lbl)

        # 3. Neutral Advice Box
        advice_frame = QFrame()
        advice_frame.setStyleSheet("""
            background-color: #0d1527;
            border-left: 3px solid #3b82f6;
            border-radius: 4px;
            padding: 8px;
        """)
        adv_layout = QVBoxLayout(advice_frame)
        adv_layout.setContentsMargins(8, 8, 8, 8)
        adv_layout.setSpacing(4)

        adv_title = QLabel("💡 ORIENTAÇÃO NEUTRA DE INVESTIGAÇÃO")
        adv_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #60a5fa;")
        adv_layout.addWidget(adv_title)

        adv_text = QLabel(item.meta.neutral_advice)
        adv_text.setWordWrap(True)
        adv_text.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        adv_layout.addWidget(adv_text)

        layout.addWidget(advice_frame)

        # 4. Checklist items
        if item.meta.checklist:
            check_title = QLabel("Itens recomendados para inspeção (sem trocar peças prematuramente):")
            check_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
            layout.addWidget(check_title)

            check_box = QVBoxLayout()
            check_box.setSpacing(3)
            check_box.setContentsMargins(8, 0, 0, 0)
            for c in item.meta.checklist:
                item_lbl = QLabel(f"•  {c}")
                item_lbl.setWordWrap(True)
                item_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
                check_box.addWidget(item_lbl)
            layout.addLayout(check_box)
