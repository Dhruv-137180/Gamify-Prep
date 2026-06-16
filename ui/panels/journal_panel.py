"""Quest Journal panel — reverse-chronological log of completed days."""
from datetime import date as _date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_DARK, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)

_DAYS_TO_SHOW = 60


class _JournalRow(QWidget):
    """One row in the journal — represents a single day."""

    def __init__(self, log: dict, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(56)

        date_str = log.get("date", "")
        p_done   = bool(log.get("project_completed"))
        t_done   = bool(log.get("theory_completed"))
        s_done   = bool(log.get("skill_completed"))
        exp      = log.get("exp_awarded", 0)
        penalty  = bool(log.get("penalty_triggered"))
        skill_n  = log.get("skill_name", "") or ""
        all_done = p_done and t_done and s_done

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)

        # Date + day name
        try:
            d = _date.fromisoformat(date_str)
            day_name = d.strftime("%a").upper()
        except Exception:
            day_name = "—"

        date_lbl = QLabel(f"{day_name}\n{date_str}")
        date_lbl.setFixedWidth(64)
        date_lbl.setAlignment(Qt.AlignCenter)
        date_lbl.setStyleSheet(
            f"color: {ACCENT_CYAN if all_done else TEXT_SECONDARY}; "
            f"font-size: 10px; font-weight: bold; background: transparent;"
        )
        lay.addWidget(date_lbl)

        # Quest badges
        badges = QHBoxLayout()
        badges.setSpacing(4)
        for label, done, color in [
            ("PRJ", p_done, SUCCESS),
            ("THY", t_done, ACCENT_CYAN),
            ("SKL", s_done, "#bb44ff"),
        ]:
            bdg = QLabel(f"[{label}]")
            bdg.setStyleSheet(
                f"color: {color if done else TEXT_MUTED}; "
                f"font-size: 9px; font-weight: bold; background: transparent;"
            )
            badges.addWidget(bdg)
        lay.addLayout(badges)

        # Skill credited
        if skill_n:
            sk = QLabel(f"▸ {skill_n}")
            sk.setStyleSheet(f"color: #bb44ff; font-size: 10px; background: transparent;")
            lay.addWidget(sk)

        lay.addStretch()

        # Status
        if penalty:
            status = QLabel("PENALTY")
            status.setStyleSheet(
                f"color: {DANGER}; font-size: 10px; font-weight: bold; background: transparent;"
            )
            lay.addWidget(status)
        elif all_done:
            combo = QLabel("COMBO ⚡" if exp >= 150 else "COMPLETE ✔")
            combo.setStyleSheet(
                f"color: {GOLD if exp >= 150 else SUCCESS}; "
                f"font-size: 10px; font-weight: bold; background: transparent;"
            )
            lay.addWidget(combo)
        else:
            quests_done = sum([p_done, t_done, s_done])
            incomplete = QLabel(f"{quests_done}/3")
            incomplete.setStyleSheet(
                f"color: {WARNING}; font-size: 10px; background: transparent;"
            )
            lay.addWidget(incomplete)

        # EXP earned
        if exp > 0:
            exp_lbl = QLabel(f"+{exp} EXP")
            exp_lbl.setStyleSheet(
                f"color: {GOLD}; font-size: 10px; background: transparent;"
            )
            exp_lbl.setFixedWidth(70)
            exp_lbl.setAlignment(Qt.AlignRight)
            lay.addWidget(exp_lbl)

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.setBrush(Qt.NoBrush)
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class JournalPanel(QWidget):
    """Scrollable reverse-chronological quest journal."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        hdr_row = QHBoxLayout()
        hdr = QLabel("[!]  QUEST  JOURNAL  —  LAST  60  DAYS")
        hdr.setObjectName("questTitle")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        hdr_row.addWidget(self._summary_lbl)
        outer.addLayout(hdr_row)

        # Column headers
        col_hdr = QWidget()
        col_hdr.setFixedHeight(20)
        ch_lay = QHBoxLayout(col_hdr)
        ch_lay.setContentsMargins(14, 0, 14, 0)
        ch_lay.setSpacing(12)
        for txt, w in [("DATE", 64), ("QUESTS", 80), ("SKILL", 80)]:
            lbl = QLabel(txt)
            lbl.setFixedWidth(w)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; letter-spacing: 2px; background: transparent;")
            ch_lay.addWidget(lbl)
        ch_lay.addStretch()
        for txt in ["STATUS", "EXP"]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; letter-spacing: 2px; background: transparent;")
            ch_lay.addWidget(lbl)
        outer.addWidget(col_hdr)

        # Scrollable rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from PySide6.QtWidgets import QFrame
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._rows_lay = QVBoxLayout(self._content)
        self._rows_lay.setContentsMargins(0, 0, 0, 0)
        self._rows_lay.setSpacing(2)
        self._rows_lay.addStretch()

        scroll.setWidget(self._content)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        # Clear existing rows (but keep the stretch)
        while self._rows_lay.count() > 1:
            item = self._rows_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today      = _date.today()
        start      = (today - timedelta(days=_DAYS_TO_SHOW - 1)).isoformat()
        logs       = db.get_quest_logs_range(start, today.isoformat())

        # Reverse order (newest first)
        rows_added = 0
        total_exp  = 0
        full_days  = 0
        for log in reversed(logs):
            row = _JournalRow(log)
            self._rows_lay.insertWidget(self._rows_lay.count() - 1, row)
            rows_added += 1
            total_exp += log.get("exp_awarded", 0)
            if (log.get("project_completed") and
                    log.get("theory_completed") and
                    log.get("skill_completed")):
                full_days += 1

        self._summary_lbl.setText(
            f"{full_days} full days  |  {total_exp:,} EXP total"
        )
