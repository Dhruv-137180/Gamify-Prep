"""Full-window rank-up celebration overlay — more dramatic than level-up, fires on rank boundary crossings."""
from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

from ui.theme import ACCENT_CYAN, BG_DARK, GOLD, RANK_COLORS, TEXT_PRIMARY, TEXT_SECONDARY, WARNING


class RankUpOverlay(QWidget):
    """
    Shows a dramatic full-screen rank-up celebration.
    Call show_rankup(old_rank, new_rank, new_level) to trigger.
    Click anywhere or wait 5 s to dismiss.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self._bg_alpha  = 0.0
        self._scan_y    = 0.0
        self._rank_color = QColor(GOLD)

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._start_fadeout)

        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(16)
        self._scan_timer.timeout.connect(self._advance_scan)

        self._build_ui()
        self._build_anims()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self._content = QWidget(self)
        lay = QVBoxLayout(self._content)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(14)
        lay.setContentsMargins(60, 40, 60, 40)

        self._lbl_warning = QLabel("! ! !  RANK  BREAKTHROUGH  ! ! !")
        self._lbl_old     = QLabel("E-RANK")
        self._lbl_arrow   = QLabel("▼")
        self._lbl_new     = QLabel("D-RANK")
        self._lbl_title   = QLabel("D-Rank Awakened")
        self._lbl_hint    = QLabel("[ click anywhere to continue ]")

        for lbl in (self._lbl_warning, self._lbl_old, self._lbl_arrow,
                    self._lbl_new, self._lbl_title, self._lbl_hint):
            lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(lbl)

        self._lbl_warning.setStyleSheet(
            f"color: {WARNING}; font-size: 18px; font-weight: bold; letter-spacing: 4px;"
        )
        self._lbl_old.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 32px; font-weight: bold; letter-spacing: 4px;"
        )
        self._lbl_arrow.setStyleSheet(
            f"color: {GOLD}; font-size: 36px;"
        )
        self._lbl_new.setStyleSheet(
            f"color: {GOLD}; font-size: 56px; font-weight: bold; letter-spacing: 8px;"
        )
        self._lbl_title.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 16px; letter-spacing: 3px;"
        )
        self._lbl_hint.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )

        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(GOLD))
        glow.setBlurRadius(50)
        glow.setOffset(0, 0)
        self._lbl_new.setGraphicsEffect(glow)

        self._opacity_fx = QGraphicsOpacityEffect(self._content)
        self._opacity_fx.setOpacity(0.0)
        self._content.setGraphicsEffect(self._opacity_fx)

    def _build_anims(self):
        self._fade_in = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setDuration(400)
        self._fade_in.setEasingCurve(QEasingCurve.OutQuad)

        self._fade_out = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setDuration(700)
        self._fade_out.setEasingCurve(QEasingCurve.InQuad)
        self._fade_out.finished.connect(self._on_fadeout_done)

        self._bg_in = QPropertyAnimation(self, b"bg_alpha")
        self._bg_in.setStartValue(0.0)
        self._bg_in.setEndValue(0.93)
        self._bg_in.setDuration(400)

        self._bg_out = QPropertyAnimation(self, b"bg_alpha")
        self._bg_out.setStartValue(0.93)
        self._bg_out.setEndValue(0.0)
        self._bg_out.setDuration(700)

    # ── bg_alpha property ──────────────────────────────────────────────

    def get_bg_alpha(self) -> float:
        return self._bg_alpha

    def set_bg_alpha(self, v: float) -> None:
        self._bg_alpha = v
        self.update()

    bg_alpha = Property(float, get_bg_alpha, set_bg_alpha)

    # ── Public ────────────────────────────────────────────────────────

    def show_rankup(self, old_rank: str, new_rank: str, new_level: int,
                    new_title: str) -> None:
        rank_color = RANK_COLORS.get(new_rank, GOLD)
        self._rank_color = QColor(rank_color)

        self._lbl_old.setText(old_rank)
        self._lbl_new.setText(new_rank)
        self._lbl_new.setStyleSheet(
            f"color: {rank_color}; font-size: 56px; font-weight: bold; letter-spacing: 8px;"
        )
        self._lbl_title.setText(new_title)

        glow = QGraphicsDropShadowEffect()
        glow.setColor(self._rank_color)
        glow.setBlurRadius(60)
        glow.setOffset(0, 0)
        self._lbl_new.setGraphicsEffect(glow)

        self._position()
        self.show()
        self.raise_()

        self._scan_y = 0.0
        self._scan_timer.start()

        self._bg_out.stop()
        self._bg_in.stop()
        self._bg_in.start()

        self._fade_out.stop()
        self._fade_in.stop()
        self._fade_in.start()

        self._auto_timer.start(5000)

    def _advance_scan(self) -> None:
        self._scan_y += 0.012
        if self._scan_y > 1.3:
            self._scan_y = -0.1
        self.update()

    # ── Dismiss ───────────────────────────────────────────────────────

    def mousePressEvent(self, _) -> None:
        self._start_fadeout()

    def _start_fadeout(self) -> None:
        self._auto_timer.stop()
        self._scan_timer.stop()
        self._fade_in.stop()
        self._fade_out.start()
        self._bg_out.start()

    def _on_fadeout_done(self) -> None:
        self.hide()

    # ── Layout ────────────────────────────────────────────────────────

    def _position(self) -> None:
        if self.parent():
            geo = self.parent().rect()
            self.setGeometry(geo)
            self._content.setGeometry(0, 0, geo.width(), geo.height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.isVisible():
            self._position()

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Dark overlay with rank tint
        bg = QColor(BG_DARK)
        bg.setAlphaF(self._bg_alpha * 0.92)
        p.fillRect(0, 0, w, h, bg)

        tint = QColor(self._rank_color)
        tint.setAlphaF(self._bg_alpha * 0.08)
        p.fillRect(0, 0, w, h, tint)

        # Horizontal scan line
        scan_px = int(self._scan_y * h)
        scan_c  = QColor(self._rank_color)
        for thickness, alpha in [(12, 15), (4, 40), (1, 180)]:
            scan_c.setAlpha(int(alpha * self._bg_alpha))
            p.setPen(QPen(scan_c, thickness))
            p.drawLine(0, scan_px, w, scan_px)

        # Vignette border in rank color
        for pw, a in [(20, 0.04), (6, 0.15), (2, 0.5), (1, 1.0)]:
            c = QColor(self._rank_color)
            c.setAlphaF(a * self._bg_alpha)
            p.setPen(QPen(c, pw))
            p.setBrush(Qt.NoBrush)
            half = pw // 2
            p.drawRect(half, half, w - pw, h - pw)

        p.end()
