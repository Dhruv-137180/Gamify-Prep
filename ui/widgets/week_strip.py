"""7-day week strip widget showing quest completion status."""
from datetime import date as _date, timedelta

from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from ui.theme import (
    ACCENT_CYAN, BG_DARK, DANGER, SUCCESS, TEXT_MUTED, TEXT_SECONDARY, WARNING,
)

_DAY_LABELS = ["M", "T", "W", "T", "F", "S", "S"]
_CELL_W = 36
_CELL_H = 54
_GAP    = 4


class WeekStrip(QWidget):
    """Horizontally laid-out 7-day strip.  Call refresh() with date/log data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cells: list[dict] = [
            {"letter": d, "symbol": "·", "color": TEXT_MUTED, "today": False}
            for d in _DAY_LABELS
        ]
        self._glow  = 0.5
        self._gdir  = 1
        total_w = 7 * _CELL_W + 6 * _GAP
        self.setFixedSize(total_w, _CELL_H)

        pulse = QTimer(self)
        pulse.timeout.connect(self._pulse)
        pulse.start(45)

    # ── Public ────────────────────────────────────────────────────────

    def refresh(self, today_str: str, logs: dict[str, dict]) -> None:
        """
        today_str: 'YYYY-MM-DD'
        logs: {date_str: quest_log_row_dict} — only the current week rows
        """
        today_date = _date.fromisoformat(today_str)
        mon        = today_date - timedelta(days=today_date.weekday())

        for i in range(7):
            d     = mon + timedelta(days=i)
            ds    = d.isoformat()
            row   = logs.get(ds)
            is_t  = ds == today_str
            is_f  = d > today_date
            cell  = self._cells[i]

            cell["today"]  = is_t
            cell["letter"] = _DAY_LABELS[i]

            if is_future := (d > today_date):
                cell["symbol"] = "·"
                cell["color"]  = TEXT_MUTED
            elif row is None:
                # Past day, no log
                cell["symbol"] = "✗"
                cell["color"]  = DANGER
            elif row.get("penalty_triggered"):
                cell["symbol"] = "✗"
                cell["color"]  = DANGER
            elif (row.get("project_completed") and
                  row.get("theory_completed")  and
                  row.get("skill_completed")):
                cell["symbol"] = "✔"
                cell["color"]  = SUCCESS
            else:
                cell["symbol"] = "●" if is_t else "○"
                cell["color"]  = ACCENT_CYAN if is_t else TEXT_SECONDARY

        self.update()

    # ── Paint ─────────────────────────────────────────────────────────

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

        for i, cell in enumerate(self._cells):
            x = i * (_CELL_W + _GAP)
            r = QRect(x, 0, _CELL_W, _CELL_H)

            bg = QColor(ACCENT_CYAN); bg.setAlpha(int(25 * self._glow)) \
                if cell["today"] else None

            # Cell background
            p.fillRect(r, QColor("#0d1a2e") if cell["today"] else QColor(BG_DARK))

            if cell["today"]:
                ga = int(60 + 70 * self._glow)
                from PySide6.QtGui import QPen
                c = QColor(ACCENT_CYAN); c.setAlpha(ga)
                p.setPen(QPen(c, 1))
                p.setBrush(Qt.NoBrush)
                p.drawRect(x, 0, _CELL_W - 1, _CELL_H - 1)

            # Day letter
            p.setFont(QFont("Consolas", 9))
            letter_color = QColor(ACCENT_CYAN) if cell["today"] else QColor(TEXT_SECONDARY)
            p.setPen(letter_color)
            p.drawText(QRect(x, 4, _CELL_W, 16), Qt.AlignCenter, cell["letter"])

            # Symbol
            sym_color = QColor(cell["color"])
            if cell["today"] and cell["symbol"] in ("●", "○"):
                sym_color.setAlpha(int(180 + 75 * self._glow))
            p.setPen(sym_color)
            p.setFont(QFont("Consolas", 14, QFont.Bold))
            p.drawText(QRect(x, 20, _CELL_W, 28), Qt.AlignCenter, cell["symbol"])

        p.end()
