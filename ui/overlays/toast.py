"""Slide-in toast notification system.  Toasts stack in the top-right corner."""
from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation,
    QSequentialAnimationGroup, Qt, QTimer,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

from ui.theme import (
    ACCENT_CYAN, BG_PANEL, BORDER_BRIGHT, DANGER, GOLD, SUCCESS, TEXT_PRIMARY, WARNING,
)

_TOAST_W = 320
_TOAST_H = 68
_MARGIN  = 10

_STYLE_MAP = {
    "info":    (ACCENT_CYAN, BORDER_BRIGHT),
    "success": (SUCCESS,     SUCCESS),
    "combo":   (GOLD,        GOLD),
    "danger":  (DANGER,      DANGER),
    "warn":    (WARNING,     WARNING),
}


class Toast(QWidget):
    """Individual toast notification."""

    def __init__(self, message: str, detail: str, style: str, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(_TOAST_W, _TOAST_H)

        fg, border = _STYLE_MAP.get(style, _STYLE_MAP["info"])
        self._border_color = QColor(border)
        self._bg_color     = QColor(BG_PANEL)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(3)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f"color: {fg}; font-size: 12px; font-weight: bold; "
            f"letter-spacing: 1px; background: transparent;"
        )
        det_lbl = QLabel(detail)
        det_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(msg_lbl)
        lay.addWidget(det_lbl)

        self._opacity_fx = QGraphicsOpacityEffect(self)
        self._opacity_fx.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_fx)

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setEasingCurve(QEasingCurve.OutBack)
        self._slide_anim.setDuration(380)

        self._fade_out = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setDuration(420)
        self._fade_out.setEasingCurve(QEasingCurve.InQuad)
        self._fade_out.finished.connect(self._on_hidden)

        self._fade_in = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setDuration(260)

        self._auto = QTimer(self)
        self._auto.setSingleShot(True)
        self._auto.timeout.connect(self.dismiss)

    # ── Public ────────────────────────────────────────────────────────

    def slide_in_at(self, x: int, y: int, timeout_ms: int = 3200) -> None:
        start_x = x + _TOAST_W + 20
        self.move(start_x, y)
        self.show()
        self.raise_()
        self._slide_anim.setStartValue(self.pos())
        self._slide_anim.setEndValue(self.__class__._mk_point(x, y))
        self._slide_anim.start()
        self._fade_in.start()
        self._auto.start(timeout_ms)

    def dismiss(self) -> None:
        self._auto.stop()
        self._fade_out.start()

    # ── Internal ──────────────────────────────────────────────────────

    def _on_hidden(self) -> None:
        self.hide()
        self.deleteLater()

    @staticmethod
    def _mk_point(x: int, y: int):
        from PySide6.QtCore import QPoint
        return QPoint(x, y)

    def paintEvent(self, _) -> None:  # noqa: N802
        from PySide6.QtGui import QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, self._bg_color)
        p.setPen(QPen(self._border_color, 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(0, 0, w - 1, h - 1)
        # Top accent stripe
        p.setPen(Qt.NoPen)
        p.setBrush(self._border_color)
        p.drawRect(0, 0, w, 3)
        p.end()


class ToastManager:
    """Manages a stack of Toast widgets anchored to the parent's top-right corner."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._active: list[Toast] = []

    def show(self, message: str, detail: str = "", style: str = "info",
             timeout: int = 3200) -> None:
        # Remove dead toasts
        self._active = [t for t in self._active if t.isVisible()]

        toast = Toast(message, detail, style, self._parent)

        pw = self._parent.width()
        x  = pw - _TOAST_W - _MARGIN
        y  = _MARGIN + len(self._active) * (_TOAST_H + 6)

        toast.slide_in_at(x, y, timeout)
        self._active.append(toast)

    def reposition(self) -> None:
        """Call on parent resize to re-stack visible toasts."""
        self._active = [t for t in self._active if t.isVisible()]
        pw = self._parent.width()
        for i, t in enumerate(self._active):
            t.move(pw - _TOAST_W - _MARGIN, _MARGIN + i * (_TOAST_H + 6))
