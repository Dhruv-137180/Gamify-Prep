"""Achievements panel — scrollable grid of badge cards."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

import database as db
from game_logic import ACHIEVEMENTS
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, BORDER_DIM, GOLD,
    SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)


class _BadgeCard(QWidget):
    """Single achievement card — lit when unlocked, dim when locked."""

    def __init__(self, achievement: dict, unlocked: bool, unlocked_date: str, parent=None):
        super().__init__(parent)
        self._unlocked = unlocked
        self._icon_color = QColor(GOLD if unlocked else TEXT_MUTED)
        self.setMinimumSize(180, 110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        icon = QLabel(achievement["icon"])
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"font-size: 22px; color: {'transparent' if not unlocked else GOLD}; background: transparent;"
        )
        lay.addWidget(icon)

        name = QLabel(achievement["name"])
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet(
            f"color: {GOLD if unlocked else TEXT_MUTED}; font-size: 10px; "
            f"font-weight: bold; letter-spacing: 1px; background: transparent;"
        )
        lay.addWidget(name)

        desc = QLabel(achievement["desc"])
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {TEXT_SECONDARY if unlocked else BORDER_DIM}; "
            f"font-size: 9px; background: transparent;"
        )
        lay.addWidget(desc)

        if unlocked and unlocked_date:
            date_lbl = QLabel(unlocked_date)
            date_lbl.setAlignment(Qt.AlignCenter)
            date_lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 8px; background: transparent;"
            )
            lay.addWidget(date_lbl)

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG_CARD))

        if self._unlocked:
            border = QColor(GOLD)
            border.setAlpha(180)
            p.setPen(QPen(border, 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(0, 0, w - 1, h - 1)
            glow = QColor(GOLD)
            glow.setAlpha(30)
            p.setPen(QPen(glow, 4))
            p.drawRect(2, 2, w - 5, h - 5)
        else:
            p.setPen(QPen(QColor(BORDER_DIM), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(0, 0, w - 1, h - 1)
        p.end()


class AchievementsPanel(QWidget):
    """Scrollable grid showing all achievements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[str, _BadgeCard] = {}
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QLabel("[!]  ACHIEVEMENT SYSTEM  —  UNLOCK ALL BADGES")
        hdr.setObjectName("questTitle")
        hdr.setContentsMargins(0, 0, 0, 8)
        outer.addWidget(hdr)

        self._progress_lbl = QLabel("0 / 20 unlocked")
        self._progress_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        outer.addWidget(self._progress_lbl)

        # Scroll area with grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from PySide6.QtWidgets import QFrame
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background: transparent;")
        self._grid = QGridLayout(content)
        self._grid.setContentsMargins(0, 8, 0, 8)
        self._grid.setSpacing(8)

        for col in range(4):
            self._grid.setColumnStretch(col, 1)

        for i, ach in enumerate(ACHIEVEMENTS):
            card = _BadgeCard(ach, False, "")
            self._grid.addWidget(card, i // 4, i % 4)
            self._cards[ach["id"]] = card

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        db_rows = {r["achievement_id"]: r for r in db.get_achievements()}
        unlocked_count = 0

        for i, ach in enumerate(ACHIEVEMENTS):
            row = db_rows.get(ach["id"], {})
            unlocked = bool(row.get("unlocked", 0))
            date_str = row.get("unlocked_date", "")
            if unlocked:
                unlocked_count += 1

            # Replace card with updated version
            old_card = self._cards.get(ach["id"])
            if old_card:
                self._grid.removeWidget(old_card)
                old_card.deleteLater()

            card = _BadgeCard(ach, unlocked, date_str)
            self._grid.addWidget(card, i // 4, i % 4)
            self._cards[ach["id"]] = card

        self._progress_lbl.setText(
            f"{unlocked_count} / {len(ACHIEVEMENTS)} unlocked"
        )
