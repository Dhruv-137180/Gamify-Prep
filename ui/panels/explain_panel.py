"""Explain-It-Out-Loud interview concept practice panel."""
from __future__ import annotations

import random
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

import database as db
from concepts import INTERVIEW_CONCEPTS
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, BORDER_DIM, BORDER_BRIGHT,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)

_RATING = {"good": SUCCESS, "partial": WARNING, "miss": DANGER}


class _StatsRow(QWidget):
    def __init__(self, concept: dict, stats: dict, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        diff_col = {"E": TEXT_MUTED, "D": ACCENT_CYAN, "C": SUCCESS,
                    "B": WARNING, "A": "#ff6600", "S": GOLD}
        diff = QLabel(concept["difficulty"])
        diff.setFixedWidth(14)
        diff.setStyleSheet(f"color: {diff_col.get(concept['difficulty'], TEXT_MUTED)}; "
                           f"font-size: 9px; background: transparent;")
        lay.addWidget(diff)

        topic = QLabel(f"[{concept['skill']}]")
        topic.setFixedWidth(80)
        topic.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9px; background: transparent;")
        lay.addWidget(topic)

        q = QLabel(concept["question"][:64] + ("…" if len(concept["question"]) > 64 else ""))
        q.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10px; background: transparent;")
        lay.addWidget(q)
        lay.addStretch()

        s = stats.get(concept["id"], {})
        attempts = s.get("attempts", 0)
        best     = s.get("best_rating", "")
        last     = s.get("last_date", "")

        att_lbl = QLabel(f"{attempts}×")
        att_lbl.setFixedWidth(28)
        att_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; background: transparent;")
        lay.addWidget(att_lbl)

        best_lbl = QLabel(best.upper() if best else "—")
        best_lbl.setFixedWidth(52)
        best_lbl.setStyleSheet(
            f"color: {_RATING.get(best, TEXT_MUTED)}; font-size: 10px; "
            f"font-weight: bold; background: transparent;"
        )
        lay.addWidget(best_lbl)

        date_lbl = QLabel(last or "—")
        date_lbl.setFixedWidth(80)
        date_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;")
        lay.addWidget(date_lbl)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class ExplainPanel(QWidget):
    """Interactive concept-practice panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._concept: dict | None = None
        self._revealed   = False
        self._start_time = 0.0

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._update_timer)

        self._build()
        self._pick_random()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        hdr = QLabel("[?]  EXPLAIN  IT  OUT  LOUD  —  INTERVIEW  PREP")
        hdr.setObjectName("questTitle")
        outer.addWidget(hdr)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_row.addWidget(QLabel("Skill:"))
        self._skill_filter = QComboBox()
        skills = sorted(set(c["skill"] for c in INTERVIEW_CONCEPTS))
        self._skill_filter.addItems(["All"] + skills)
        self._skill_filter.setFixedWidth(130)
        filter_row.addWidget(self._skill_filter)

        filter_row.addWidget(QLabel("Difficulty:"))
        self._diff_filter = QComboBox()
        self._diff_filter.addItems(["All", "E", "D", "C", "B", "A", "S"])
        self._diff_filter.setFixedWidth(70)
        filter_row.addWidget(self._diff_filter)

        self._next_btn = QPushButton("NEXT CONCEPT")
        self._next_btn.setFixedWidth(130)
        self._next_btn.clicked.connect(self._pick_random)
        filter_row.addWidget(self._next_btn)

        filter_row.addStretch()
        outer.addLayout(filter_row)

        # ── Practice area ──────────────────────────────────────────────────
        practice = QGroupBox("CONCEPT QUESTION")
        p_lay = QVBoxLayout(practice)
        p_lay.setSpacing(8)

        # Meta row
        meta_row = QHBoxLayout()
        self._skill_lbl = QLabel("")
        self._skill_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        self._diff_lbl  = QLabel("")
        self._diff_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 10px; font-weight: bold;")
        self._timer_lbl = QLabel("00:00")
        self._timer_lbl.setStyleSheet(f"color: {WARNING}; font-size: 12px; font-weight: bold;")
        meta_row.addWidget(self._skill_lbl)
        meta_row.addWidget(self._diff_lbl)
        meta_row.addStretch()
        meta_row.addWidget(self._timer_lbl)
        p_lay.addLayout(meta_row)

        # Question
        self._question_lbl = QLabel("")
        self._question_lbl.setWordWrap(True)
        self._question_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: bold; "
            f"padding: 10px; background: {BG_CARD}; border: 1px solid {BORDER_BRIGHT}; border-radius: 3px;"
        )
        self._question_lbl.setMinimumHeight(70)
        p_lay.addWidget(self._question_lbl)

        # Reveal button
        self._reveal_btn = QPushButton("REVEAL ANSWER")
        self._reveal_btn.setObjectName("warnBtn")
        self._reveal_btn.setFixedHeight(38)
        self._reveal_btn.clicked.connect(self._reveal)
        p_lay.addWidget(self._reveal_btn)

        # Answer (hidden until reveal)
        self._answer_edit = QTextEdit()
        self._answer_edit.setReadOnly(True)
        self._answer_edit.setFixedHeight(140)
        self._answer_edit.setStyleSheet(
            f"background: {BG_CARD}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER_DIM}; font-size: 11px; padding: 6px;"
        )
        self._answer_edit.hide()
        p_lay.addWidget(self._answer_edit)

        # Rating row
        self._rate_row = QWidget()
        rate_lay = QHBoxLayout(self._rate_row)
        rate_lay.setContentsMargins(0, 0, 0, 0)
        rate_lay.setSpacing(8)

        rate_lay.addWidget(QLabel("Your performance:"))

        for key, label, color in [
            ("good",    "GOOD",    SUCCESS),
            ("partial", "PARTIAL", WARNING),
            ("miss",    "MISS",    DANGER),
        ]:
            btn = QPushButton(label)
            btn.setFixedWidth(90)
            btn.setStyleSheet(f"color: {color}; border-color: {color}; font-size: 10px;")
            btn.clicked.connect(lambda _, k=key: self._rate(k))
            rate_lay.addWidget(btn)

        rate_lay.addStretch()
        self._rate_row.hide()
        p_lay.addWidget(self._rate_row)

        # Result label
        self._result_lbl = QLabel("")
        self._result_lbl.setAlignment(Qt.AlignCenter)
        self._result_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; font-weight: bold;")
        self._result_lbl.hide()
        p_lay.addWidget(self._result_lbl)

        outer.addWidget(practice)

        # ── Stats table ────────────────────────────────────────────────────
        stats_grp = QGroupBox("CONCEPT STATS")
        s_lay     = QVBoxLayout(stats_grp)
        s_lay.setContentsMargins(4, 8, 4, 4)
        s_lay.setSpacing(0)

        # Header
        hdr_row = QHBoxLayout()
        for text, width in [("DIFF", 14), ("SKILL", 80), ("QUESTION", 0),
                             ("×", 28), ("BEST", 52), ("LAST", 80)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; letter-spacing: 1px;")
            if width:
                lbl.setFixedWidth(width)
            hdr_row.addWidget(lbl)
            if not width:
                hdr_row.addStretch()
        hdr_row.setContentsMargins(8, 0, 8, 4)
        s_lay.addLayout(hdr_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(180)
        from PySide6.QtWidgets import QFrame
        scroll.setFrameShape(QFrame.NoFrame)

        self._stats_content = QWidget()
        self._stats_layout  = QVBoxLayout(self._stats_content)
        self._stats_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_layout.setSpacing(1)
        self._stats_layout.addStretch()
        scroll.setWidget(self._stats_content)
        s_lay.addWidget(scroll)
        outer.addWidget(stats_grp)

        self._refresh_stats()

    # ── Concept selection ─────────────────────────────────────────────────────

    def _filtered_pool(self) -> list[dict]:
        skill = self._skill_filter.currentText()
        diff  = self._diff_filter.currentText()
        pool  = INTERVIEW_CONCEPTS
        if skill != "All":
            pool = [c for c in pool if c["skill"] == skill]
        if diff != "All":
            pool = [c for c in pool if c["difficulty"] == diff]
        return pool or INTERVIEW_CONCEPTS

    def _pick_random(self):
        pool = self._filtered_pool()
        self._concept  = random.choice(pool)
        self._revealed = False
        self._start_time = time.monotonic()

        diff_col = {"E": TEXT_MUTED, "D": ACCENT_CYAN, "C": SUCCESS,
                    "B": WARNING, "A": "#ff6600", "S": GOLD}
        self._skill_lbl.setText(f"[{self._concept['skill']}]")
        self._diff_lbl.setText(f"DIFFICULTY: {self._concept['difficulty']}")
        self._diff_lbl.setStyleSheet(
            f"color: {diff_col.get(self._concept['difficulty'], ACCENT_CYAN)}; "
            f"font-size: 10px; font-weight: bold;"
        )
        self._question_lbl.setText(self._concept["question"])
        self._answer_edit.hide()
        self._answer_edit.setPlainText("")
        self._rate_row.hide()
        self._result_lbl.hide()
        self._reveal_btn.show()
        self._reveal_btn.setEnabled(True)
        self._timer_lbl.setText("00:00")
        self._ticker.start(1000)

    # ── Interaction ───────────────────────────────────────────────────────────

    def _update_timer(self):
        elapsed = int(time.monotonic() - self._start_time)
        mins, secs = divmod(elapsed, 60)
        self._timer_lbl.setText(f"{mins:02d}:{secs:02d}")

    def _reveal(self):
        if not self._concept:
            return
        self._ticker.stop()
        self._revealed = True
        self._answer_edit.setPlainText(self._concept["answer"])
        self._answer_edit.show()
        self._rate_row.show()
        self._reveal_btn.hide()
        self._result_lbl.hide()

    def _rate(self, rating: str):
        if not self._concept:
            return
        elapsed = max(1, int(time.monotonic() - self._start_time))
        db.log_concept_attempt(self._concept["id"], rating, elapsed)

        color = _RATING.get(rating, TEXT_PRIMARY)
        labels = {"good": "✔ WELL DONE — Keep it up!",
                  "partial": "~ PARTIAL — Review the key points",
                  "miss": "✗ MISS — Study this concept again"}
        self._result_lbl.setText(labels.get(rating, ""))
        self._result_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        self._result_lbl.show()
        self._rate_row.hide()

        self._refresh_stats()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _refresh_stats(self):
        while self._stats_layout.count() > 1:
            item = self._stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = db.get_concept_stats()
        for concept in INTERVIEW_CONCEPTS:
            row = _StatsRow(concept, stats)
            self._stats_layout.insertWidget(self._stats_layout.count() - 1, row)

    def refresh(self):
        self._refresh_stats()
