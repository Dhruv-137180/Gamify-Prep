"""
Full-window crimson penalty zone overlay.
Usage:
    penalty.start(remaining_seconds)   — show & start countdown
    penalty.cleared signal             — emitted when time expires OR user marks complete
"""
from datetime import datetime, timezone, timedelta

from PySide6.QtCore import Property, QPropertyAnimation, QEasingCurve, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ui.theme import (
    DANGER, GOLD, PENALTY_ACCENT, PENALTY_BG, PENALTY_BORDER,
    PENALTY_DIM, PENALTY_PANEL, TEXT_PRIMARY, TEXT_SECONDARY,
)

_PROMPT = (
    "PUNISHMENT PROTOCOL ENGAGED\n\n"
    "Complete ONE of the following:\n"
    "  ▸  Solve a data-structures / scripting challenge\n"
    "  ▸  Write a full digital-logic breakdown\n"
    "     (e.g. async FIFO, CDC synchronisation, arbitration)\n\n"
    "The System is watching."
)


class PenaltyZoneWidget(QWidget):
    """Covers the entire parent widget with a crimson penalty screen."""

    cleared = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self._remaining  = 0.0
        self._pulsing    = False   # True when < 5 minutes left
        self._pulse_show = True
        self._entry_alpha = 0.0

        self._build_ui()
        self._build_tick_timer()
        self._build_pulse_timer()
        self._build_entry_anim()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(18)
        lay.setContentsMargins(60, 40, 60, 40)

        # ── Warning header ──
        header = QLabel("⚠  PENALTY  ZONE  ACTIVATED  ⚠")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            f"color: {PENALTY_ACCENT}; font-size: 22px; font-weight: bold; "
            f"letter-spacing: 6px; background: transparent;"
        )
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(PENALTY_ACCENT))
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        header.setGraphicsEffect(glow)
        lay.addWidget(header)

        lay.addSpacing(10)

        # ── Timer display ──
        self._timer_lbl = QLabel("45:00")
        self._timer_lbl.setAlignment(Qt.AlignCenter)
        self._timer_lbl.setStyleSheet(
            f"color: {PENALTY_ACCENT}; font-size: 72px; font-weight: bold; "
            f"letter-spacing: 6px; background: transparent;"
        )
        timer_glow = QGraphicsDropShadowEffect()
        timer_glow.setColor(QColor(PENALTY_ACCENT))
        timer_glow.setBlurRadius(40)
        timer_glow.setOffset(0, 0)
        self._timer_lbl.setGraphicsEffect(timer_glow)
        lay.addWidget(self._timer_lbl)

        # ── Subtitle ──
        sub = QLabel("RECOVERY TIME REMAINING")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            f"color: {PENALTY_DIM}; font-size: 11px; letter-spacing: 4px; background: transparent;"
        )
        lay.addWidget(sub)

        lay.addSpacing(16)

        # ── Prompt box ──
        self._prompt_lbl = QLabel(_PROMPT)
        self._prompt_lbl.setAlignment(Qt.AlignLeft)
        self._prompt_lbl.setWordWrap(True)
        self._prompt_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; "
            f"background-color: {PENALTY_PANEL}; "
            f"border: 1px solid {PENALTY_BORDER}; "
            f"border-radius: 3px; padding: 16px;"
        )
        self._prompt_lbl.setMaximumWidth(560)
        lay.addWidget(self._prompt_lbl, alignment=Qt.AlignCenter)

        lay.addSpacing(20)

        # ── Complete button ──
        self._complete_btn = QPushButton("■  PENALTY COMPLETE — UNLOCK SYSTEM  ■")
        self._complete_btn.setObjectName("penaltyBtn")
        self._complete_btn.setStyleSheet(
            f"QPushButton {{ "
            f"  background-color: {PENALTY_PANEL}; "
            f"  color: {PENALTY_ACCENT}; "
            f"  border: 2px solid {PENALTY_ACCENT}; "
            f"  border-radius: 3px; "
            f"  padding: 12px 30px; "
            f"  font-size: 13px; "
            f"  font-weight: bold; "
            f"  letter-spacing: 2px; "
            f"  font-family: Consolas, monospace; "
            f"}} "
            f"QPushButton:hover {{ background-color: {PENALTY_ACCENT}; color: #000; }} "
        )
        self._complete_btn.setMaximumWidth(500)
        self._complete_btn.clicked.connect(self._on_complete)
        lay.addWidget(self._complete_btn, alignment=Qt.AlignCenter)

        # ── Streak warning ──
        warn = QLabel("WARNING: Streak has been reset to 0")
        warn.setAlignment(Qt.AlignCenter)
        warn.setStyleSheet(
            f"color: {PENALTY_DIM}; font-size: 10px; letter-spacing: 1px; background: transparent;"
        )
        lay.addWidget(warn)

    def _build_tick_timer(self):
        self._tick = QTimer(self)
        self._tick.setInterval(250)   # 4 Hz for smooth countdown
        self._tick.timeout.connect(self._on_tick)

    def _build_pulse_timer(self):
        # Makes the timer text blink when < 5 minutes
        self._pulse_t = QTimer(self)
        self._pulse_t.setInterval(550)
        self._pulse_t.timeout.connect(self._blink_timer)

    def _build_entry_anim(self):
        self._entry_anim = QPropertyAnimation(self, b"entry_alpha")
        self._entry_anim.setStartValue(0.0)
        self._entry_anim.setEndValue(1.0)
        self._entry_anim.setDuration(600)
        self._entry_anim.setEasingCurve(QEasingCurve.OutCubic)

    # ── entry_alpha property (drives bg fade-in) ──────────────────────

    def get_entry_alpha(self) -> float:
        return self._entry_alpha

    def set_entry_alpha(self, v: float) -> None:
        self._entry_alpha = v
        self.update()

    entry_alpha = Property(float, get_entry_alpha, set_entry_alpha)

    # ── Public ────────────────────────────────────────────────────────

    def start(self, remaining_seconds: float) -> None:
        self._remaining = max(0.0, remaining_seconds)
        self._update_timer_display()
        self._position()
        self.show()
        self.raise_()
        self._tick.start()
        if self._remaining < 300:
            self._pulse_t.start()
        self._entry_anim.start()

    def stop(self) -> None:
        self._tick.stop()
        self._pulse_t.stop()
        self.hide()

    # ── Internal ──────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        self._remaining -= 0.25
        if self._remaining <= 0:
            self._remaining = 0
            self._update_timer_display()
            self._on_complete()
            return
        if self._remaining < 300 and not self._pulse_t.isActive():
            self._pulse_t.start()
        self._update_timer_display()

    def _blink_timer(self) -> None:
        self._pulse_show = not self._pulse_show
        self._timer_lbl.setVisible(self._pulse_show)

    def _on_complete(self) -> None:
        self.stop()
        self.cleared.emit()

    def _update_timer_display(self) -> None:
        secs   = int(self._remaining)
        mm, ss = divmod(secs, 60)
        self._timer_lbl.setText(f"{mm:02d}:{ss:02d}")
        # Colour gradient: red → dark red as time ticks down
        if secs < 300:
            self._timer_lbl.setStyleSheet(
                f"color: {DANGER}; font-size: 72px; font-weight: bold; "
                f"letter-spacing: 6px; background: transparent;"
            )
        self._timer_lbl.setVisible(True)
        self._pulse_show = True

    def _position(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self._position()

    # ── Paint (crimson background) ────────────────────────────────────

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        alpha = int(245 * self._entry_alpha)

        # Deep crimson gradient
        grad = QLinearGradient(0, 0, 0, h)
        top = QColor(PENALTY_BG); top.setAlpha(alpha)
        bot = QColor("#0a0002"); bot.setAlpha(alpha)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bot)
        p.fillRect(0, 0, w, h, grad)

        # Vignette border
        for pw, a_frac in [(20, 0.06), (10, 0.12), (4, 0.25), (2, 0.5), (1, 1.0)]:
            c = QColor(PENALTY_ACCENT)
            c.setAlpha(int(90 * a_frac * self._entry_alpha))
            p.setPen(QPen(c, pw))
            p.setBrush(Qt.NoBrush)
            half = pw // 2
            p.drawRect(half, half, w - pw, h - pw)

        p.end()
