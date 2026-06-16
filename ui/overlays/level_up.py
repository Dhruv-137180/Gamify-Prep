"""Full-window level-up celebration overlay with fade-in / fade-out animation."""
from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation,
    QSequentialAnimationGroup, Qt, QTimer,
)
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from ui.theme import (
    ACCENT_CYAN, BG_DARK, GOLD, RANK_COLORS, SUCCESS,
    TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)


class LevelUpOverlay(QWidget):
    """
    Child of the main window's central widget.
    Call show_levelup() to animate; click anywhere or wait 4 s to dismiss.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self._bg_alpha  = 0.0
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._start_fadeout)

        self._build_ui()
        self._build_animations()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(10)

        self._lbl_flash    = QLabel("⚡  LEVEL  UP  ⚡")
        self._lbl_levels   = QLabel("LVL 1  →  LVL 2")
        self._lbl_rank_chg = QLabel("")
        self._lbl_rewards  = QLabel("+150 EXP   +70 GOLD")
        self._lbl_hint     = QLabel("[ click anywhere to continue ]")

        self._lbl_flash.setAlignment(Qt.AlignCenter)
        self._lbl_levels.setAlignment(Qt.AlignCenter)
        self._lbl_rank_chg.setAlignment(Qt.AlignCenter)
        self._lbl_rewards.setAlignment(Qt.AlignCenter)
        self._lbl_hint.setAlignment(Qt.AlignCenter)

        self._lbl_flash.setStyleSheet(
            f"color: {GOLD}; font-size: 36px; font-weight: bold; letter-spacing: 8px;"
        )
        self._lbl_levels.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 28px; font-weight: bold; letter-spacing: 4px;"
        )
        self._lbl_rank_chg.setStyleSheet(
            f"color: {SUCCESS}; font-size: 18px; font-weight: bold; letter-spacing: 2px;"
        )
        self._lbl_rewards.setStyleSheet(
            f"color: {WARNING}; font-size: 14px; letter-spacing: 2px;"
        )
        self._lbl_hint.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )

        for lbl in (self._lbl_flash, self._lbl_levels, self._lbl_rank_chg,
                    self._lbl_rewards, self._lbl_hint):
            lay.addWidget(lbl)

        # Glow effects on key labels
        for lbl, color in [
            (self._lbl_flash, GOLD),
            (self._lbl_levels, ACCENT_CYAN),
        ]:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            fx = QGraphicsDropShadowEffect()
            fx.setColor(QColor(color))
            fx.setBlurRadius(30)
            fx.setOffset(0, 0)
            lbl.setGraphicsEffect(fx)

        # Opacity wrapper so we can fade the whole content
        self._content = QWidget(self)
        content_lay = QVBoxLayout(self._content)
        content_lay.setAlignment(Qt.AlignCenter)
        content_lay.setContentsMargins(60, 40, 60, 40)
        content_lay.setSpacing(10)
        for lbl in (self._lbl_flash, self._lbl_levels, self._lbl_rank_chg,
                    self._lbl_rewards, self._lbl_hint):
            content_lay.addWidget(lbl)

        self._opacity_fx = QGraphicsOpacityEffect(self._content)
        self._opacity_fx.setOpacity(0.0)
        self._content.setGraphicsEffect(self._opacity_fx)

    def _build_animations(self):
        # Fade-in: bg_alpha 0→1, content opacity 0→1
        self._fade_in = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setDuration(320)
        self._fade_in.setEasingCurve(QEasingCurve.OutQuad)

        # Fade-out: content opacity 1→0
        self._fade_out = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setDuration(700)
        self._fade_out.setEasingCurve(QEasingCurve.InQuad)
        self._fade_out.finished.connect(self._on_fadeout_done)

        # bg_alpha property drives the dark overlay opacity
        self._bg_anim_in = QPropertyAnimation(self, b"bg_alpha")
        self._bg_anim_in.setStartValue(0.0)
        self._bg_anim_in.setEndValue(0.88)
        self._bg_anim_in.setDuration(320)
        self._bg_anim_in.setEasingCurve(QEasingCurve.OutQuad)

        self._bg_anim_out = QPropertyAnimation(self, b"bg_alpha")
        self._bg_anim_out.setStartValue(0.88)
        self._bg_anim_out.setEndValue(0.0)
        self._bg_anim_out.setDuration(700)

    # ── bg_alpha property (drives paintEvent) ─────────────────────────

    def get_bg_alpha(self) -> float:
        return self._bg_alpha

    def set_bg_alpha(self, v: float) -> None:
        self._bg_alpha = v
        self.update()

    bg_alpha = Property(float, get_bg_alpha, set_bg_alpha)

    # ── Public ────────────────────────────────────────────────────────

    def show_levelup(
        self,
        old_lvl: int, new_lvl: int,
        old_rank: str, new_rank: str,
        exp_gained: int, gold_gained: int,
    ) -> None:
        self._lbl_levels.setText(f"LVL {old_lvl}   →   LVL {new_lvl}")
        if new_rank != old_rank:
            self._lbl_rank_chg.setText(f"RANK UP!   {old_rank}  →  {new_rank}")
            rank_color = RANK_COLORS.get(new_rank, ACCENT_CYAN)
            self._lbl_rank_chg.setStyleSheet(
                f"color: {rank_color}; font-size: 18px; font-weight: bold; letter-spacing: 2px;"
            )
        else:
            self._lbl_rank_chg.setText(f"[ {new_rank} ]")
            self._lbl_rank_chg.setStyleSheet(
                f"color: {ACCENT_CYAN}; font-size: 16px; letter-spacing: 2px;"
            )
        self._lbl_rewards.setText(f"+{exp_gained} EXP   ·   +{gold_gained} GOLD")

        self._position()
        self.show()
        self.raise_()

        self._bg_anim_in.stop(); self._bg_anim_in.start()
        self._fade_out.stop()
        self._fade_in.stop();   self._fade_in.start()

        self._auto_timer.start(3800)

    def _position(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())
            pw = self.parent().width()
            ph = self.parent().height()
            self._content.setGeometry(0, 0, pw, ph)

    # ── Dismiss ───────────────────────────────────────────────────────

    def mousePressEvent(self, _) -> None:
        self._start_fadeout()

    def _start_fadeout(self) -> None:
        self._auto_timer.stop()
        self._fade_in.stop()
        self._fade_out.start()
        self._bg_anim_out.start()

    def _on_fadeout_done(self) -> None:
        self.hide()

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        c = QColor(0, 0, 0)
        c.setAlphaF(self._bg_alpha)
        p.fillRect(self.rect(), c)
        p.end()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self._position()
