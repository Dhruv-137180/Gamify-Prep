"""Compact skill-progression table widget."""
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_DARK, BG_PANEL,
    BORDER_DIM, GOLD, RANK_COLORS, SUCCESS, TEXT_MUTED, TEXT_SECONDARY, TEXT_PRIMARY,
    WARNING,
)
from game_logic import get_skill_rank, SKILL_RANK_THRESHOLDS

_RANK_MAX = {
    "F": 50, "E": 120, "D": 220, "C": 350, "B": 520, "A": 750, "S": 1000,
}
_RANK_COLOR = {
    "F": TEXT_MUTED,
    "E": TEXT_SECONDARY,
    "D": ACCENT_CYAN,
    "C": SUCCESS,
    "B": WARNING,
    "A": "#ff6600",
    "S": GOLD,
}


class _MiniBar(QWidget):
    """Tiny horizontal progress bar for skill proficiency."""

    def __init__(self, points: int, rank: str, parent=None):
        super().__init__(parent)
        self._pct   = 0.0
        self._color = QColor(ACCENT_CYAN)
        self.setFixedSize(130, 8)
        self.update_values(points, rank)

    def update_values(self, points: int, rank: str) -> None:
        # Next rank's threshold is the 100% mark
        rank_max = _RANK_MAX.get(rank, 1000)
        prev_max = 0
        for threshold, r in reversed(SKILL_RANK_THRESHOLDS):
            if r == rank:
                # Find previous rank's floor
                idx = list(reversed(SKILL_RANK_THRESHOLDS)).index((threshold, r))
                if idx + 1 < len(SKILL_RANK_THRESHOLDS):
                    prev_max = list(reversed(SKILL_RANK_THRESHOLDS))[idx + 1][0]
                break
        span = rank_max - prev_max
        self._pct   = max(0.0, min(1.0, (points - prev_max) / max(span, 1)))
        self._color = QColor(_RANK_COLOR.get(rank, ACCENT_CYAN))
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG_DARK))
        fill_w = int(w * self._pct)
        if fill_w > 1:
            grad = QLinearGradient(0, 0, w, 0)
            c_dim = QColor(self._color); c_dim.setAlpha(80)
            grad.setColorAt(0.0, c_dim)
            grad.setColorAt(1.0, self._color)
            p.fillRect(0, 0, fill_w, h, grad)
        p.end()


class SkillTable(QWidget):
    """Shows all 9 DV skills with rank, points, and mini progress bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, tuple] = {}   # skill_name → (rank_lbl, pts_lbl, bar)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area for the rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        from PySide6.QtWidgets import QFrame
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: {BG_PANEL};")
        grid = QVBoxLayout(content)
        grid.setContentsMargins(10, 6, 10, 6)
        grid.setSpacing(4)

        from database import SKILLS
        for skill in SKILLS:
            row = self._make_row(skill)
            grid.addWidget(row)
            grid.addWidget(self._make_div())

        grid.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _make_row(self, skill_name: str) -> QWidget:
        row = QWidget()
        hl  = QHBoxLayout(row)
        hl.setContentsMargins(4, 3, 4, 3)
        hl.setSpacing(8)

        # Skill name
        name_lbl = QLabel(skill_name)
        name_lbl.setFixedWidth(90)
        name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px;")
        hl.addWidget(name_lbl)

        # Mini bar
        bar = _MiniBar(0, "F")
        hl.addWidget(bar)

        # Rank label
        rank_lbl = QLabel("F")
        rank_lbl.setFixedWidth(22)
        rank_lbl.setAlignment(Qt.AlignCenter)
        rank_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold;")
        hl.addWidget(rank_lbl)

        # Points
        pts_lbl = QLabel("0 pts")
        pts_lbl.setFixedWidth(52)
        pts_lbl.setAlignment(Qt.AlignRight)
        pts_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        hl.addWidget(pts_lbl)

        self._rows[skill_name] = (rank_lbl, pts_lbl, bar)
        return row

    def _make_div(self) -> QWidget:
        d = QWidget()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background: {BG_DARK};")
        return d

    def refresh(self, skills: list[dict]) -> None:
        """Called with the result of database.get_all_skills()."""
        for s in skills:
            name  = s["skill_name"]
            pts   = s["proficiency_points"]
            rank  = s["current_rank"]
            if name not in self._rows:
                continue
            rank_lbl, pts_lbl, bar = self._rows[name]
            color = _RANK_COLOR.get(rank, TEXT_MUTED)
            rank_lbl.setText(rank)
            rank_lbl.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: bold;"
            )
            pts_lbl.setText(f"{pts} pts")
            bar.update_values(pts, rank)
