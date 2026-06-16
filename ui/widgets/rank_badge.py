"""Animated rank badge widget with colour-coded neon glow pulse."""
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import RANK_COLORS, ACCENT_CYAN, BG_DARK


class RankBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rank  = "E-RANK"
        self._color = QColor(ACCENT_CYAN)
        self._glow  = 0.5
        self._gdir  = 1

        self.setMinimumSize(130, 42)

        pulse = QTimer(self)
        pulse.timeout.connect(self._pulse)
        pulse.start(38)   # ~26 fps

    # ── Public ────────────────────────────────────────────────────────────

    def set_rank(self, rank: str) -> None:
        self._rank  = rank
        self._color = QColor(RANK_COLORS.get(rank, ACCENT_CYAN))
        self.update()

    # ── Internal ──────────────────────────────────────────────────────────

    def _pulse(self) -> None:
        self._glow += self._gdir * 0.018
        if self._glow >= 1.0:
            self._gdir = -1
        elif self._glow <= 0.15:
            self._gdir = 1
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor(BG_DARK))

        ga = int(45 + 100 * self._glow)
        for pw, scale in [(10, 0.10), (6, 0.20), (3, 0.45), (1, 1.0)]:
            c = QColor(self._color)
            c.setAlpha(int(ga * scale))
            p.setPen(QPen(c, pw))
            p.setBrush(Qt.NoBrush)
            half = pw // 2
            p.drawRect(half, half, w - pw, h - pw)

        p.setPen(self._color)
        f = QFont("Consolas", 16, QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        p.setFont(f)
        p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._rank)
        p.end()
