"""
Quest card widget — neon-bordered card with completion flash animation.
Emits completion_requested(type, skill_name); main window writes to DB and calls
animate_completion() to trigger the visual flash.
"""
from PySide6.QtCore import Qt, QSequentialAnimationGroup, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ui.theme import (
    ACCENT_CYAN, BG_CARD, BORDER_BRIGHT, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)
from game_logic import EXP_TABLE, GOLD_TABLE

_TAG_COLORS = {
    "PROJECT": "#ff7700",
    "THEORY":  "#00aaff",
    "SKILL":   "#bb44ff",
}
_TAG_DESC = {
    "PROJECT": "Execute Daily Target Block",
    "THEORY":  "Master Comp Arc / Bus Protocols",
    "SKILL":   "Implement Dynamic Constraints",
}


class QuestCard(QWidget):
    """Clickable quest card.  Click the card (not the checkbox) to trigger completion."""

    completion_requested = Signal(str, str)   # (quest_type, skill_name or "")
    undo_requested       = Signal(str)        # (quest_type)

    def __init__(self, quest_type: str, parent=None):
        super().__init__(parent)
        self._type  = quest_type
        self._done  = False
        self._glow  = 0.25
        self._gdir  = 1
        self._hovering = False

        self.setMinimumHeight(64)
        self.setCursor(Qt.PointingHandCursor)

        self._build_layout()
        self._build_flash_overlay()
        self._start_glow_pulse()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(12)

        # Checkbox (display-only — whole card is the click target)
        self._chk = QCheckBox()
        self._chk.setEnabled(False)
        self._chk.setAttribute(Qt.WA_TransparentForMouseEvents)
        top.addWidget(self._chk)

        # Tag label
        tag_color = _TAG_COLORS.get(self._type, ACCENT_CYAN)
        tag_lbl = QLabel(f"[{self._type}]")
        tag_lbl.setStyleSheet(
            f"color: {tag_color}; font-weight: bold; letter-spacing: 1px; font-size: 11px;"
        )
        tag_lbl.setFixedWidth(80)
        top.addWidget(tag_lbl)

        # Description
        self._desc_lbl = QLabel(_TAG_DESC.get(self._type, ""))
        self._desc_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        top.addWidget(self._desc_lbl)
        top.addStretch()

        # Reward hint
        exp  = EXP_TABLE.get(self._type, 0)
        gold = GOLD_TABLE.get(self._type, 0)
        rwd = QLabel(f"+{exp} EXP  +{gold} GOLD")
        rwd.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        top.addWidget(rwd)

        # Status label
        self._status_lbl = QLabel("[ INCOMPLETE ]")
        self._status_lbl.setStyleSheet(f"color: {DANGER}; font-size: 11px; font-weight: bold;")
        self._status_lbl.setFixedWidth(125)
        self._status_lbl.setAlignment(Qt.AlignRight)
        top.addWidget(self._status_lbl)

        # Undo button (hidden until completed)
        from PySide6.QtWidgets import QPushButton
        self._undo_btn = QPushButton("UNDO")
        self._undo_btn.setFixedSize(52, 24)
        self._undo_btn.setStyleSheet(
            f"color: {WARNING}; border: 1px solid {WARNING}; "
            f"font-size: 9px; padding: 0; background: transparent;"
        )
        self._undo_btn.clicked.connect(lambda: self.undo_requested.emit(self._type))
        self._undo_btn.hide()
        top.addWidget(self._undo_btn)

        outer.addLayout(top)

        # Skill selector row (SKILL quest only)
        self._skill_combo = None
        if self._type == "SKILL":
            skill_row = QHBoxLayout()
            skill_row.setSpacing(8)
            skill_row.addSpacing(36)  # align with description
            skill_row.addWidget(QLabel("▸ skill:"))

            from database import SKILLS
            self._skill_combo = QComboBox()
            self._skill_combo.addItem("-- SELECT SKILL --")
            self._skill_combo.addItems(SKILLS)
            self._skill_combo.setFixedWidth(200)
            self._skill_combo.setToolTip("Choose which skill this session credits")
            skill_row.addWidget(self._skill_combo)
            skill_row.addStretch()
            outer.addLayout(skill_row)

    def _build_flash_overlay(self):
        self._flash_ov = QWidget(self)
        self._flash_ov.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._flash_ov.setAttribute(Qt.WA_TranslucentBackground)
        self._flash_ov.setStyleSheet("background-color: #00e87a;")
        self._flash_fx = QGraphicsOpacityEffect(self._flash_ov)
        self._flash_fx.setOpacity(0.0)
        self._flash_ov.setGraphicsEffect(self._flash_fx)
        self._flash_ov.setGeometry(self.rect())
        self._flash_ov.hide()
        self._seq_ref = None  # keep animation alive

    def _start_glow_pulse(self):
        t = QTimer(self)
        t.timeout.connect(self._pulse)
        t.start(55)

    # ── Public ────────────────────────────────────────────────────────

    def set_completed(self, done: bool) -> None:
        """Update visual state from DB (no animation)."""
        self._done = done
        self._chk.setChecked(done)
        if done:
            self._status_lbl.setText("[ COMPLETED ]")
            self._status_lbl.setStyleSheet(
                f"color: {SUCCESS}; font-size: 11px; font-weight: bold;"
            )
            self._undo_btn.show()
            if self._skill_combo:
                self._skill_combo.setEnabled(False)
        else:
            self._status_lbl.setText("[ INCOMPLETE ]")
            self._status_lbl.setStyleSheet(
                f"color: {DANGER}; font-size: 11px; font-weight: bold;"
            )
            self._undo_btn.hide()
            if self._skill_combo:
                self._skill_combo.setEnabled(True)
        self.update()

    def animate_completion(self) -> None:
        """Green flash animation triggered after DB write succeeds."""
        self.set_completed(True)
        self._flash_ov.setGeometry(self.rect())
        self._flash_ov.show()
        self._flash_ov.raise_()

        seq = QSequentialAnimationGroup(self)

        a1 = QPropertyAnimation(self._flash_fx, b"opacity")
        a1.setStartValue(0.0)
        a1.setEndValue(0.50)
        a1.setDuration(140)
        a1.setEasingCurve(QEasingCurve.OutQuad)

        a2 = QPropertyAnimation(self._flash_fx, b"opacity")
        a2.setStartValue(0.50)
        a2.setEndValue(0.0)
        a2.setDuration(680)
        a2.setEasingCurve(QEasingCurve.InCubic)

        seq.addAnimation(a1)
        seq.addAnimation(a2)
        seq.finished.connect(self._flash_ov.hide)
        seq.start()
        self._seq_ref = seq

    def get_skill_name(self) -> str:
        if self._skill_combo is None:
            return ""
        idx = self._skill_combo.currentIndex()
        return self._skill_combo.currentText() if idx > 0 else ""

    def highlight_skill_missing(self) -> None:
        """Flash the skill combo red to signal user must pick a skill first."""
        if self._skill_combo:
            self._skill_combo.setStyleSheet(
                f"border: 2px solid {DANGER}; color: {DANGER};"
            )
            QTimer.singleShot(
                900, lambda: self._skill_combo.setStyleSheet("")
            )

    # ── Interaction ───────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self._done:
            return
        if self._type == "SKILL":
            skill = self.get_skill_name()
            if not skill:
                self.highlight_skill_missing()
                return
            self.completion_requested.emit(self._type, skill)
        else:
            self.completion_requested.emit(self._type, "")

    def enterEvent(self, _) -> None:
        self._hovering = True
        self.update()

    def leaveEvent(self, _) -> None:
        self._hovering = False
        self.update()

    # ── Animation ─────────────────────────────────────────────────────

    def _pulse(self) -> None:
        if not self._done:
            speed = 0.025 if self._hovering else 0.018
            self._glow += self._gdir * speed
            if self._glow >= 1.0:
                self._gdir = -1
            elif self._glow <= 0.08:
                self._gdir = 1
            self.update()

    # ── Resize ────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._flash_ov.setGeometry(self.rect())

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor(BG_CARD))

        if self._done:
            base_color = QColor(SUCCESS)
            ga = 160
        elif self._hovering:
            base_color = QColor(ACCENT_CYAN)
            ga = 200
        else:
            base_color = QColor(BORDER_BRIGHT)
            ga = int(30 + 90 * self._glow)

        for pw, scale in [(5, 0.12), (3, 0.28), (1, 1.0)]:
            c = QColor(base_color)
            c.setAlpha(int(ga * scale))
            p.setPen(QPen(c, pw))
            p.setBrush(Qt.NoBrush)
            half = pw // 2
            p.drawRect(half, half, w - pw, h - pw)

        p.end()
