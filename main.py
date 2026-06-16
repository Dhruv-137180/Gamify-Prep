"""Entry point.  Run with --dev to open the Dev Mode console automatically."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

import database as db
from ui.main_window import MainWindow


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Hunter's System Interface")

    win = MainWindow(dev_mode="--dev" in sys.argv)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
