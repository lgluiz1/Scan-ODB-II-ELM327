"""Visual status widget with LED indicator and descriptive status tags.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class StatusBadge(QFrame):
    """
    Card displaying status with LED light indicator, title and dynamic detail.
    States: 'disconnected', 'connecting', 'connected', 'error'
    """

    def __init__(self, icon_emoji: str, title: str, default_sub: str = "Desconectado", parent=None):
        super().__init__(parent)
        self.icon_emoji = icon_emoji
        self.title_text = title

        self.setObjectName("statusCard")
        self.setStyleSheet("""
            QFrame#statusCard {
                background-color: #131c2e;
                border: 1px solid #233149;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Icon / Emoji label
        self.lbl_icon = QLabel(self.icon_emoji)
        self.lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(self.lbl_icon)

        # Text column
        v_box = QVBoxLayout()
        v_box.setSpacing(1)
        v_box.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(self.title_text)
        self.lbl_title.setStyleSheet("font-size: 10px; text-transform: uppercase; color: #94a3b8; font-weight: 700; background: transparent;")
        v_box.addWidget(self.lbl_title)

        self.lbl_sub = QLabel(default_sub)
        self.lbl_sub.setStyleSheet("font-size: 11px; font-weight: 600; color: #cbd5e1; background: transparent;")
        v_box.addWidget(self.lbl_sub)

        layout.addLayout(v_box)
        layout.addStretch()

        # LED Indicator Dot
        self.led_indicator = QLabel()
        self.led_indicator.setFixedSize(10, 10)
        layout.addWidget(self.led_indicator)

        self.set_state("disconnected", default_sub)

    def set_state(self, state: str, detail_text: str = ""):
        """
        Updates indicator appearance.
        state: 'disconnected', 'connecting', 'connected', 'error'
        """
        if detail_text:
            self.lbl_sub.setText(detail_text)

        if state == "connected":
            # Bright glowing green
            self.led_indicator.setStyleSheet("""
                background-color: #10b981;
                border-radius: 7px;
                border: 2px solid #34d399;
            """)
            self.lbl_sub.setStyleSheet("font-size: 13px; font-weight: 600; color: #4ade80;")
            self.setStyleSheet("""
                QFrame#statusCard {
                    background-color: #13282b;
                    border: 1px solid #059669;
                    border-radius: 8px;
                }
            """)
        elif state == "connecting":
            # Amber pulsing/yellow
            self.led_indicator.setStyleSheet("""
                background-color: #f59e0b;
                border-radius: 7px;
                border: 2px solid #fbbf24;
            """)
            self.lbl_sub.setStyleSheet("font-size: 13px; font-weight: 600; color: #fbbf24;")
            self.setStyleSheet("""
                QFrame#statusCard {
                    background-color: #2b2613;
                    border: 1px solid #d97706;
                    border-radius: 8px;
                }
            """)
        elif state == "error":
            # Bright red
            self.led_indicator.setStyleSheet("""
                background-color: #ef4444;
                border-radius: 7px;
                border: 2px solid #f87171;
            """)
            self.lbl_sub.setStyleSheet("font-size: 13px; font-weight: 600; color: #f87171;")
            self.setStyleSheet("""
                QFrame#statusCard {
                    background-color: #2b1318;
                    border: 1px solid #dc2626;
                    border-radius: 8px;
                }
            """)
        else:  # disconnected
            # Slate gray
            self.led_indicator.setStyleSheet("""
                background-color: #475569;
                border-radius: 7px;
                border: 2px solid #64748b;
            """)
            self.lbl_sub.setStyleSheet("font-size: 13px; font-weight: 600; color: #94a3b8;")
            self.setStyleSheet("""
                QFrame#statusCard {
                    background-color: #131c2e;
                    border: 1px solid #233149;
                    border-radius: 8px;
                }
            """)
