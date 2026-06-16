"""Animated neon EXP progress bar with glowing edge and fill animation."""
from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRect, Qt, QTimer,
)
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import ACCENT_BLUE, ACCENT_CYAN, BG_CARD, TEXT_PRIMARY


class NeonExpBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill  = 0.0   # 0.0–1.0
        self._text  = "0 / 100 EXP"
        self._glow  = 0.5
        self._gdir  = 1

        self.setMinimumHeight(26)
        self.setMaximumHeight(32)

        # Fill animation
        self._anim = QPropertyAnimation(self, b"fill_pct")
        self._anim.setDuration(950)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # Glow pulse
        pulse = QTimer(self)
        pulse.timeout.connect(self._pulse)
        pulse.start(45)

    # ── Animatable property ───────────────────────────────────────────────

    def get_fill_pct(self) -> float:
        return self._fill

    def set_fill_pct(self, v: float) -> None:
        self._fill = max(0.0, min(1.0, v))
        self.update()

    fill_pct = Property(float, get_fill_pct, set_fill_pct)

    # ── Public ────────────────────────────────────────────────────────────

    def set_progress(self, current: int, maximum: int, animate: bool = True) -> None:
        self._text = f"{current:,} / {maximum:,} EXP"
        target = current / max(maximum, 1)
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._fill)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self.set_fill_pct(target)

    # ── Internal ──────────────────────────────────────────────────────────

    def _pulse(self) -> None:
        self._glow += self._gdir * 0.022
        if self._glow >= 1.0:
            self._gdir = -1
        elif self._glow <= 0.15:
            self._gdir = 1
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ── Background ──
        p.fillRect(0, 0, w, h, QColor(BG_CARD))

        # ── Glow border (multiple pen widths) ──
        ga = int(55 + 90 * self._glow)
        for pw, alpha_scale in [(6, 0.15), (4, 0.30), (2, 0.60), (1, 1.0)]:
            c = QColor(ACCENT_CYAN)
            c.setAlpha(int(ga * alpha_scale))
            p.setPen(QPen(c, pw))
            p.setBrush(Qt.NoBrush)
            half = pw // 2
            p.drawRect(half, half, w - pw, h - pw)

        # ── Gradient fill ──
        fill_w = int((w - 4) * self._fill)
        if fill_w > 2:
            grad = QLinearGradient(2, 0, w - 2, 0)
            grad.setColorAt(0.00, QColor("#001440"))
            grad.setColorAt(0.55, QColor(ACCENT_BLUE))
            grad.setColorAt(1.00, QColor(ACCENT_CYAN))
            p.fillRect(2, 2, fill_w, h - 4, grad)

            # Leading-edge glow
            eg = QLinearGradient(2 + fill_w - 22, 0, 2 + fill_w + 4, 0)
            eg.setColorAt(0.0, QColor(0, 212, 255, 0))
            eg.setColorAt(1.0, QColor(0, 212, 255, 210))
            p.fillRect(max(2, 2 + fill_w - 22), 2, min(26, fill_w), h - 4, eg)

        # ── Label ──
        p.setPen(QColor(TEXT_PRIMARY))
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, self._text)
        p.end()
