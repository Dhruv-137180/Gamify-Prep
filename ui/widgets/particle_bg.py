"""Animated particle background — sits behind content, transparent to mouse."""
import math
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from ui.theme import ACCENT_CYAN


class ParticleBg(QWidget):
    """Subtle drifting-star effect. Place as a sibling behind content widgets."""

    def __init__(self, parent=None, count: int = 45):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._enabled  = True
        self._particles: list[dict] = []
        self._count    = count
        self._seed()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._step)
        self._anim.start(50)   # 20 FPS — cheap enough

    # ── Public ────────────────────────────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.update()

    # ── Private ───────────────────────────────────────────────────────────────

    def _seed(self):
        rng = random.Random(0xDEAD)
        for _ in range(self._count):
            self._particles.append({
                "x":     rng.uniform(0.0, 1.0),
                "y":     rng.uniform(0.0, 1.0),
                "vx":    rng.uniform(-4e-4, 4e-4),
                "vy":    rng.uniform(-2e-4, 2e-4),
                "size":  rng.uniform(1.0, 2.8),
                "alpha": rng.randint(15, 70),
                "phase": rng.uniform(0.0, math.tau),
            })

    def _step(self):
        if not self._enabled:
            return
        for pt in self._particles:
            pt["x"] = (pt["x"] + pt["vx"]) % 1.0
            pt["y"] = (pt["y"] + pt["vy"]) % 1.0
            pt["phase"] += 0.025
        self.update()

    def paintEvent(self, _):
        if not self._enabled:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        base  = QColor(ACCENT_CYAN)

        for pt in self._particles:
            alpha = int(pt["alpha"] * (0.55 + 0.45 * math.sin(pt["phase"])))
            c = QColor(base)
            c.setAlpha(alpha)
            painter.setPen(c)
            painter.setBrush(c)
            px = int(pt["x"] * w)
            py = int(pt["y"] * h)
            r  = pt["size"]
            painter.drawEllipse(int(px - r), int(py - r), int(r * 2), int(r * 2))

        painter.end()
