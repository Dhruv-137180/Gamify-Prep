"""Compact Pomodoro focus-timer widget."""
from datetime import date

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QPushButton, QWidget

import database as db
from ui.theme import ACCENT_CYAN, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING

_FOCUS_SECS = 25 * 60
_BREAK_SECS = 5  * 60


class PomodoroWidget(QWidget):
    """25-min focus / 5-min break Pomodoro timer; logs completed sessions to DB."""

    session_completed = Signal(int)   # emits today's completed count

    def __init__(self, parent=None):
        super().__init__(parent)
        self._remaining = _FOCUS_SECS
        self._running   = False
        self._on_break  = False

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tick)

        self._build()
        self._update_display()
        self._refresh_count()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(14)

        # Timer display
        left = QVBoxLayout()
        left.setSpacing(1)

        self._mode_lbl = QLabel("FOCUS")
        self._mode_lbl.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 9px; letter-spacing: 2px; background: transparent;"
        )
        left.addWidget(self._mode_lbl)

        self._time_lbl = QLabel("25:00")
        self._time_lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 24px; font-weight: bold; background: transparent;"
        )
        left.addWidget(self._time_lbl)
        lay.addLayout(left)

        # Controls
        self._start_btn = QPushButton("START")
        self._start_btn.setFixedSize(72, 28)
        self._start_btn.setStyleSheet(
            f"color: {SUCCESS}; border-color: {SUCCESS}; font-size: 9px; padding: 2px 6px;"
        )
        self._start_btn.clicked.connect(self._on_start_pause)

        self._reset_btn = QPushButton("RESET")
        self._reset_btn.setFixedSize(64, 24)
        self._reset_btn.setStyleSheet(
            f"color: {TEXT_MUTED}; border-color: {TEXT_MUTED}; font-size: 9px; padding: 2px 6px;"
        )
        self._reset_btn.clicked.connect(self._on_reset)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.addWidget(self._start_btn)
        btn_col.addWidget(self._reset_btn)
        lay.addLayout(btn_col)

        # Today's count
        right = QVBoxLayout()
        right.setSpacing(0)
        right.setAlignment(Qt.AlignCenter)

        self._count_lbl = QLabel("0")
        self._count_lbl.setAlignment(Qt.AlignCenter)
        self._count_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: bold; background: transparent;"
        )
        lbl_today = QLabel("POMS TODAY")
        lbl_today.setAlignment(Qt.AlignCenter)
        lbl_today.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; background: transparent;")

        right.addWidget(self._count_lbl)
        right.addWidget(lbl_today)
        lay.addLayout(right)

        lay.addStretch()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _refresh_count(self):
        count = db.get_pomodoro_count(date.today().isoformat())
        self._count_lbl.setText(str(count))

    def _update_display(self):
        mins, secs = divmod(self._remaining, 60)
        self._time_lbl.setText(f"{mins:02d}:{secs:02d}")
        if self._on_break:
            self._mode_lbl.setText("BREAK")
            self._time_lbl.setStyleSheet(
                f"color: {SUCCESS}; font-size: 24px; font-weight: bold; background: transparent;"
            )
        else:
            self._mode_lbl.setText("FOCUS")
            self._time_lbl.setStyleSheet(
                f"color: {GOLD}; font-size: 24px; font-weight: bold; background: transparent;"
            )

    def _tick(self):
        if self._remaining > 0:
            self._remaining -= 1
            self._update_display()
            return

        # Session ended
        self._ticker.stop()
        self._running = False
        self._start_btn.setText("START")

        if not self._on_break:
            db.log_pomodoro(date.today().isoformat(), 25, completed=True)
            self._refresh_count()
            count = db.get_pomodoro_count(date.today().isoformat())
            self.session_completed.emit(count)
            self._on_break  = True
            self._remaining = _BREAK_SECS
        else:
            self._on_break  = False
            self._remaining = _FOCUS_SECS

        self._update_display()

    def _on_start_pause(self):
        if self._running:
            self._ticker.stop()
            self._running = False
            self._start_btn.setText("RESUME")
        else:
            self._ticker.start(1000)
            self._running = True
            self._start_btn.setText("PAUSE")

    def _on_reset(self):
        self._ticker.stop()
        self._running   = False
        self._on_break  = False
        self._remaining = _FOCUS_SECS
        self._start_btn.setText("START")
        self._update_display()
