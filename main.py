import sys
import os
import datetime
import traceback

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from ui.styles import DARK_THEME_QSS
from app.config import APP_NAME, APP_VERSION


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Logs unexpected exceptions to crash_debug.log instead of silent abort."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_debug.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] UNCAUGHT EXCEPTION:\n{err}\n")
    except Exception:
        pass

    print("ERRO INESPERADO:", err, file=sys.stderr)


sys.excepthook = global_exception_handler


def main():
    # Setup High-DPI support for Windows displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
