"""Prestige overlay — dramatic full-screen celebration when the player prestiges."""
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ui.theme import BG_DARK, DANGER, GOLD, TEXT_PRIMARY, TEXT_SECONDARY


class PrestigeOverlay(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(16)

        self._num_lbl = QLabel("")
        self._num_lbl.setAlignment(Qt.AlignCenter)
        self._num_lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 52px; font-weight: bold; "
            f"letter-spacing: 10px; background: transparent;"
        )
        lay.addWidget(self._num_lbl)

        self._title_lbl = QLabel("")
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self._title_lbl.setStyleSheet(
            f"color: {DANGER}; font-size: 20px; font-weight: bold; "
            f"letter-spacing: 5px; background: transparent;"
        )
        lay.addWidget(self._title_lbl)

        self._sub_lbl = QLabel("")
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; "
            f"letter-spacing: 2px; background: transparent;"
        )
        lay.addWidget(self._sub_lbl)

        lay.addSpacing(24)

        dismiss = QPushButton("[ CONTINUE YOUR JOURNEY ]")
        dismiss.setFixedWidth(260)
        dismiss.setStyleSheet(
            f"color: {GOLD}; border: 1px solid {GOLD}; "
            f"background: transparent; font-size: 12px; padding: 10px 20px;"
        )
        dismiss.clicked.connect(self.hide)
        lay.addWidget(dismiss, alignment=Qt.AlignCenter)

        self._scan_y = 0
        self._phase  = 0.0

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)

        self._auto_close = QTimer(self)
        self._auto_close.setSingleShot(True)
        self._auto_close.timeout.connect(self.hide)

    def show_prestige(self, prestige_num: int, title: str, level_reached: int, gold_kept: int):
        self._num_lbl.setText(f"PRESTIGE  {prestige_num}")
        self._title_lbl.setText(title.upper() if title else "REBORN")
        self._sub_lbl.setText(
            f"Reached Level {level_reached}  ·  {gold_kept:,} Gold carried forward"
        )
        if self.parent():
            self.setGeometry(self.parent().rect())
        self._scan_y = 0
        self._phase  = 0.0
        self._anim.start(16)
        self._auto_close.start(10_000)
        self.show()
        self.raise_()

    def _tick(self):
        self._scan_y  = (self._scan_y + 4) % max(1, self.height())
        self._phase  += 0.04
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 210))

        glow = QRadialGradient(self.width() / 2, self.height() / 2, self.width() * 0.55)
        pulse = 0.5 + 0.5 * math.sin(self._phase)
        glow.setColorAt(0.0, QColor(255, 215, 0, int(30 + 20 * pulse)))
        glow.setColorAt(0.6, QColor(180, 50, 0, int(15 * pulse)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        pen = QPen(QColor(255, 215, 0, 50), 2)
        p.setPen(pen)
        p.drawLine(0, self._scan_y, self.width(), self._scan_y)
        p.end()

    def hideEvent(self, event):
        if hasattr(self, "_anim"):
            self._anim.stop()
            self._auto_close.stop()
        super().hideEvent(event)
