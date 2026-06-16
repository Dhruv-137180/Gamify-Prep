"""Monthly calendar heatmap panel."""
from datetime import date as _date
import calendar as _cal

from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_DARK, BG_PANEL,
    BORDER_DIM, DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY,
)

_CELL  = 44
_GAP   = 4
_DAYS  = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


class _CalGrid(QWidget):
    """Draws a monthly calendar heatmap."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._year  = _date.today().year
        self._month = _date.today().month
        self._cells: list[dict] = []
        self._setFixedGridSize()

    def _setFixedGridSize(self):
        w = 7 * _CELL + 6 * _GAP + 2
        h = 7 * _CELL + 6 * _GAP + 2   # max 6 week rows + header row
        self.setFixedSize(w, h)

    def load_month(self, year: int, month: int) -> None:
        self._year  = year
        self._month = month
        self._cells = []

        logs = {r["day"]: r for r in db.get_month_logs(year, month)}
        today = _date.today()

        first_weekday = _date(year, month, 1).weekday()  # 0=Mon
        days_in_month = _cal.monthrange(year, month)[1]

        # Leading blanks
        for _ in range(first_weekday):
            self._cells.append({"day": 0, "state": "blank"})

        for d in range(1, days_in_month + 1):
            log = logs.get(d, {})
            day_date = _date(year, month, d)
            if day_date > today:
                state = "future"
            elif log.get("completed", 0) >= log.get("total", 1) and log.get("total", 0) > 0:
                state = "full"
            elif log.get("completed", 0) > 0:
                state = "partial"
            elif day_date < today:
                state = "missed"
            else:
                state = "today"
            self._cells.append({
                "day":    d,
                "state":  state,
                "is_today": day_date == today,
                "completed": log.get("completed", 0),
                "total":     log.get("total", 0),
            })

        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        _STATE_COLOR = {
            "full":    QColor(SUCCESS),
            "partial": QColor(GOLD),
            "missed":  QColor(DANGER),
            "today":   QColor(ACCENT_CYAN),
            "future":  QColor(BG_DARK),
            "blank":   QColor(0, 0, 0, 0),
        }

        # Day-of-week headers
        p.setFont(QFont("Consolas", 8))
        for col, day in enumerate(_DAYS):
            x = col * (_CELL + _GAP)
            c = QColor(TEXT_SECONDARY)
            p.setPen(c)
            p.drawText(QRect(x, 0, _CELL, 18), Qt.AlignCenter, day)

        # Cells (start y at row 1 = after header)
        row_y_offset = 22
        for idx, cell in enumerate(self._cells):
            col = idx % 7
            row = idx // 7
            x   = col * (_CELL + _GAP)
            y   = row * (_CELL + _GAP) + row_y_offset

            if cell["state"] == "blank":
                continue

            bg = QColor(_STATE_COLOR.get(cell["state"], QColor(BG_DARK)))
            if cell["state"] in ("full", "partial", "missed"):
                dim_bg = QColor(bg)
                dim_bg.setAlpha(40)
                p.fillRect(x, y, _CELL, _CELL, QColor(BG_CARD))
                p.fillRect(x, y, _CELL, _CELL, dim_bg)
            else:
                dim_bg = QColor(BG_CARD)
                p.fillRect(x, y, _CELL, _CELL, dim_bg)

            # Border
            if cell["is_today"]:
                border = QColor(ACCENT_CYAN)
                border.setAlpha(220)
                p.setPen(QPen(border, 2))
            else:
                border = QColor(bg) if cell["state"] in ("full", "partial", "missed") else QColor(BORDER_DIM)
                border.setAlpha(120)
                p.setPen(QPen(border, 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(x, y, _CELL - 1, _CELL - 1)

            # Day number
            p.setFont(QFont("Consolas", 9, QFont.Bold if cell["is_today"] else QFont.Normal))
            txt_color = QColor(bg)
            if cell["state"] in ("future", "today"):
                txt_color = QColor(TEXT_SECONDARY if cell["state"] == "future" else ACCENT_CYAN)
            p.setPen(txt_color)
            p.drawText(QRect(x, y + 4, _CELL, 16), Qt.AlignCenter, str(cell["day"]))

            # Completion fraction
            if cell["state"] in ("full", "partial", "missed") and cell["total"] > 0:
                frac = f"{cell['completed']}/{cell['total']}"
                p.setFont(QFont("Consolas", 7))
                p.setPen(QColor(bg))
                p.drawText(QRect(x, y + _CELL - 16, _CELL, 14), Qt.AlignCenter, frac)

        p.end()


class CalendarPanel(QWidget):
    """Monthly heatmap calendar with prev/next month navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        today = _date.today()
        self._year  = today.year
        self._month = today.month
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        hdr = QLabel("[!]  QUEST  CALENDAR  —  MONTHLY  OVERVIEW")
        hdr.setObjectName("questTitle")
        outer.addWidget(hdr)

        # Navigation row
        nav = QHBoxLayout()
        self._prev_btn = QPushButton("◀  PREV")
        self._prev_btn.setFixedWidth(90)
        self._prev_btn.clicked.connect(self._go_prev)
        self._month_lbl = QLabel("")
        self._month_lbl.setAlignment(Qt.AlignCenter)
        self._month_lbl.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 14px; font-weight: bold; letter-spacing: 2px;"
        )
        self._next_btn = QPushButton("NEXT  ▶")
        self._next_btn.setFixedWidth(90)
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._prev_btn)
        nav.addStretch()
        nav.addWidget(self._month_lbl)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        outer.addLayout(nav)

        # Legend
        leg = QHBoxLayout()
        leg.setSpacing(16)
        for color, label in [
            (SUCCESS, "All done"),
            (GOLD,    "Partial"),
            (DANGER,  "Missed"),
            (ACCENT_CYAN, "Today"),
        ]:
            dot = QLabel("■")
            dot.setStyleSheet(f"color: {color}; font-size: 14px; background: transparent;")
            txt = QLabel(label)
            txt.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; background: transparent;")
            leg.addWidget(dot)
            leg.addWidget(txt)
        leg.addStretch()
        outer.addLayout(leg)

        # Grid
        grid_container = QWidget()
        grid_container.setStyleSheet(f"background: {BG_PANEL}; border-radius: 3px;")
        grid_lay = QHBoxLayout(grid_container)
        grid_lay.setContentsMargins(12, 12, 12, 12)

        self._grid = _CalGrid()
        grid_lay.addWidget(self._grid, alignment=Qt.AlignHCenter)
        outer.addWidget(grid_container)
        outer.addStretch()

    def _go_prev(self) -> None:
        if self._month == 1:
            self._year -= 1
            self._month = 12
        else:
            self._month -= 1
        self.refresh()

    def _go_next(self) -> None:
        if self._month == 12:
            self._year += 1
            self._month = 1
        else:
            self._month += 1
        self.refresh()

    def refresh(self) -> None:
        month_name = _cal.month_name[self._month].upper()
        self._month_lbl.setText(f"{month_name}  {self._year}")
        self._grid.load_month(self._year, self._month)
        today = _date.today()
        self._next_btn.setEnabled(
            not (self._year == today.year and self._month == today.month)
        )
