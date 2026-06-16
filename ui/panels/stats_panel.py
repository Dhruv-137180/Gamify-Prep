"""Statistics panel — custom-drawn bar charts, metrics, and export."""
from datetime import date as _date, timedelta

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_DARK, BG_PANEL, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)


class _BarChart(QWidget):
    """Generic vertical bar chart drawn with QPainter."""

    def __init__(self, bars: list[tuple[str, float, str]], title: str,
                 max_val: float = None, parent=None):
        """
        bars: list of (label, value, color_hex)
        title: chart title
        max_val: if None, use max of values
        """
        super().__init__(parent)
        self._bars   = bars
        self._title  = title
        self._max    = max_val or max((v for _, v, _ in bars), default=1) or 1
        self.setMinimumHeight(160)

    def update_data(self, bars: list[tuple[str, float, str]], max_val: float = None) -> None:
        self._bars  = bars
        self._max   = max_val or max((v for _, v, _ in bars), default=1) or 1
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        if not self._bars:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        p.fillRect(0, 0, w, h, QColor(BG_CARD))

        title_h   = 22
        label_h   = 18
        chart_h   = h - title_h - label_h - 4
        n         = len(self._bars)
        bar_w     = max(6, (w - 20) // n - 4)
        gap       = max(2, (w - 20 - n * bar_w) // max(n - 1, 1))

        # Title
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.setPen(QColor(TEXT_SECONDARY))
        p.drawText(QRect(0, 2, w, title_h), Qt.AlignCenter, self._title)

        # Bars
        for i, (label, val, color) in enumerate(self._bars):
            fill_h = int(chart_h * min(val / self._max, 1.0))
            x      = 10 + i * (bar_w + gap)
            y      = title_h + (chart_h - fill_h)

            # Bar background
            p.fillRect(x, title_h, bar_w, chart_h, QColor(BG_DARK))

            # Gradient fill
            if fill_h > 0:
                grad = QLinearGradient(x, y + fill_h, x, y)
                c    = QColor(color)
                dim  = QColor(c); dim.setAlpha(80)
                grad.setColorAt(0.0, dim)
                grad.setColorAt(1.0, c)
                p.fillRect(x, y, bar_w, fill_h, grad)

            # Value label at top of bar
            if val > 0:
                p.setFont(QFont("Consolas", 7))
                p.setPen(QColor(color))
                val_str = str(int(val)) if val == int(val) else f"{val:.0f}"
                p.drawText(QRect(x - 4, y - 14, bar_w + 8, 14), Qt.AlignCenter, val_str)

            # X-axis label
            p.setFont(QFont("Consolas", 7))
            p.setPen(QColor(TEXT_MUTED))
            p.drawText(
                QRect(x - 4, title_h + chart_h + 2, bar_w + 8, label_h),
                Qt.AlignCenter, label
            )

        # Baseline
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.drawLine(8, title_h + chart_h, w - 8, title_h + chart_h)

        p.end()


class _StatCard(QWidget):
    """Small metric card with a big number and label."""

    def __init__(self, label: str, value: str = "0", color: str = ACCENT_CYAN, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self.setMinimumWidth(120)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignCenter)

        self._val_lbl = QLabel(value)
        self._val_lbl.setAlignment(Qt.AlignCenter)
        self._val_lbl.setStyleSheet(
            f"color: {color}; font-size: 26px; font-weight: bold; background: transparent;"
        )
        lay.addWidget(self._val_lbl)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9px; letter-spacing: 1px; background: transparent;")
        lay.addWidget(lbl)

    def set_value(self, value: str) -> None:
        self._val_lbl.setText(value)

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(0, 0, self.width() - 1, self.height() - 1)
        p.end()


class StatsPanel(QWidget):
    """Statistics overview with charts and summary cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # Header row
        hdr_row = QHBoxLayout()
        hdr = QLabel("[!]  HUNTER  STATISTICS  —  PROGRESS  OVERVIEW")
        hdr.setObjectName("questTitle")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        export_btn = QPushButton("EXPORT  JSON")
        export_btn.clicked.connect(self._on_export)
        hdr_row.addWidget(export_btn)
        outer.addLayout(hdr_row)

        # Summary cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self._card_level   = _StatCard("LEVEL",        "1",   GOLD)
        self._card_streak  = _StatCard("STREAK",       "0",   WARNING)
        self._card_best    = _StatCard("BEST STREAK",  "0",   WARNING)
        self._card_gold    = _StatCard("GOLD EARNED",  "0",   GOLD)
        self._card_boss    = _StatCard("BOSS CLEARS",  "0",   ACCENT_CYAN)
        self._card_rate    = _StatCard("30-DAY RATE",  "0%",  SUCCESS)
        for card in (self._card_level, self._card_streak, self._card_best,
                     self._card_gold, self._card_boss, self._card_rate):
            cards_row.addWidget(card)
        outer.addLayout(cards_row)

        # EXP chart (last 14 days)
        self._exp_chart = _BarChart([], "EXP EARNED — LAST 14 DAYS")
        self._exp_chart.setMinimumHeight(180)
        outer.addWidget(self._exp_chart)

        # Skill chart
        self._skill_chart = _BarChart([], "SKILL PROFICIENCY POINTS")
        self._skill_chart.setMinimumHeight(180)
        outer.addWidget(self._skill_chart)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Progress", "hunter_progress.json", "JSON Files (*.json)"
        )
        if path:
            try:
                db.export_progress_json(path)
                from ui.theme import SUCCESS
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Export Failed", str(e))

    def refresh(self) -> None:
        hunter = db.get_hunter()
        skills = db.get_all_skills()

        self._card_level.set_value(str(hunter.get("level", 1)))
        self._card_streak.set_value(str(hunter.get("streak", 0)))
        self._card_best.set_value(str(hunter.get("best_streak", 0)))
        self._card_gold.set_value(f"{hunter.get('gold', 0):,}")
        self._card_boss.set_value(str(db.get_boss_completions_count()))

        # 30-day completion rate
        today      = _date.today()
        thirty_ago = (today - timedelta(days=29)).isoformat()
        logs = db.get_quest_logs_range(thirty_ago, today.isoformat())
        done_days = sum(
            1 for lg in logs
            if lg.get("project_completed") and
               lg.get("theory_completed") and
               lg.get("skill_completed")
        )
        rate = int(done_days / 30 * 100)
        self._card_rate.set_value(f"{rate}%")

        # EXP chart — last 14 days
        exp_bars = []
        for i in range(13, -1, -1):
            d     = today - timedelta(days=i)
            ds    = d.isoformat()
            log   = next((lg for lg in logs if lg["date"] == ds), None)
            exp   = log.get("exp_awarded", 0) if log else 0
            label = d.strftime("%d")
            color = SUCCESS if exp > 0 else BORDER_DIM
            exp_bars.append((label, exp, color))
        self._exp_chart.update_data(exp_bars)

        # Skill chart
        _RANK_COLOR = {"F": TEXT_MUTED, "E": TEXT_SECONDARY, "D": ACCENT_CYAN,
                       "C": SUCCESS, "B": WARNING, "A": "#ff6600", "S": GOLD}
        skill_bars = [
            (
                s["skill_name"][:3],
                s["proficiency_points"],
                _RANK_COLOR.get(s["current_rank"], ACCENT_CYAN),
            )
            for s in skills
        ]
        max_pts = max((s["proficiency_points"] for s in skills), default=1) or 1
        self._skill_chart.update_data(skill_bars, max_val=max(max_pts, 50))
