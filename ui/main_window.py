"""
Hunter's System Interface — main window (all features).
Tabs: QUESTS | JOURNAL | CALENDAR | STATS | BADGES | SHOP | TASKS
"""
from __future__ import annotations

from datetime import date as _date, datetime, timedelta, timezone

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSlider,
    QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget, QMenu,
)

import database as db
import date_helper
import game_logic
from audio_engine import AudioEngine
from ui.overlays.level_up    import LevelUpOverlay
from ui.overlays.rank_up     import RankUpOverlay
from ui.overlays.penalty_zone import PenaltyZoneWidget
from ui.overlays.toast       import ToastManager
from ui.overlays.prestige_overlay  import PrestigeOverlay
from ui.panels.achievements_panel  import AchievementsPanel
from ui.panels.calendar_panel      import CalendarPanel
from ui.panels.explain_panel       import ExplainPanel
from ui.panels.journal_panel       import JournalPanel
from ui.panels.settings_panel      import SettingsPanel
from ui.panels.shop_panel          import ShopPanel
from ui.panels.skill_tree_panel    import SkillTreePanel
from ui.panels.stats_panel         import StatsPanel
from ui.panels.task_editor_panel   import TaskEditorPanel
from ui.widgets.exp_bar       import NeonExpBar
from ui.widgets.particle_bg   import ParticleBg
from ui.widgets.pomodoro_widget import PomodoroWidget
from ui.widgets.quest_card    import QuestCard
from ui.widgets.rank_badge    import RankBadge
from ui.widgets.skill_table   import SkillTable
from ui.widgets.week_strip    import WeekStrip
from ui.theme import (
    ACCENT_CYAN, BG_DARK, BG_PANEL, BORDER_DIM, BORDER_BRIGHT,
    DANGER, GOLD, RANK_COLORS,
    SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
    get_stylesheet,
)

# ── Nav tab indices ────────────────────────────────────────────────────────────
_TAB_QUESTS   = 0
_TAB_JOURNAL  = 1
_TAB_CALENDAR = 2
_TAB_STATS    = 3
_TAB_BADGES   = 4
_TAB_SHOP     = 5
_TAB_TASKS    = 6
_TAB_EXPLAIN  = 7
_TAB_TREE     = 8
_TAB_SETTINGS = 9

_NAV_LABELS = [
    "QUESTS", "JOURNAL", "CALENDAR", "STATS",
    "BADGES", "SHOP", "TASKS", "EXPLAIN", "SKILLS", "SETTINGS",
]


def _make_tray_icon() -> QIcon:
    """Draw a tiny cyan ■ as the tray icon."""
    from PySide6.QtGui import QPixmap
    img = QImage(16, 16, QImage.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.fillRect(2, 2, 12, 12, QColor(ACCENT_CYAN))
    p.end()
    return QIcon(QPixmap.fromImage(img))


class MainWindow(QWidget):
    """Top-level window with navigation tabs."""

    def __init__(self, dev_mode: bool = False):
        super().__init__()
        self._dev_mode  = dev_mode
        self._dev_panel = None
        self._audio     = AudioEngine()
        self._current_theme = db.get_setting("theme", "cyan")

        self.setWindowTitle("■  HUNTER'S  SYSTEM  INTERFACE  ■  DV QUEST")
        self.setMinimumSize(980, 720)
        self.resize(1060, 800)
        self.setStyleSheet(get_stylesheet(self._current_theme))

        self._build_ui()
        self._setup_overlays()
        self._setup_shortcuts()
        self._setup_tray()
        self._setup_timers()

        self._audio.set_state("idle")
        self._check_rollover()
        self._refresh()

        if dev_mode:
            QTimer.singleShot(200, self._open_dev_panel)

    # ═══════════════════════════════════════════════════════════════════════
    # UI construction
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(6)

        root.addWidget(self._mk_header())
        root.addWidget(self._mk_sep())
        root.addWidget(self._mk_exp_row())
        root.addWidget(self._mk_nav_bar())
        root.addWidget(self._mk_sep())
        root.addWidget(self._mk_content_stack(), stretch=1)

    # ── Header ──────────────────────────────────────────────────────────────

    def _mk_header(self) -> QWidget:
        frame = QWidget()
        frame.setObjectName("headerFrame")
        frame.setStyleSheet(
            f"QWidget#headerFrame {{"
            f"  background-color: {BG_PANEL};"
            f"  border: 1px solid #0088bb;"
            f"  border-radius: 3px;"
            f"}}"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 10, 16, 10)

        left = QVBoxLayout()
        left.setSpacing(2)
        self._status_lbl = QLabel("STATUS: ACTIVE")
        self._status_lbl.setObjectName("statusOK")
        self._player_lbl = QLabel("PLAYER: PARIN MISTRY")
        self._player_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        left.addWidget(self._status_lbl)
        left.addWidget(self._player_lbl)
        lay.addLayout(left)
        lay.addStretch()

        right = QHBoxLayout()
        right.setSpacing(16)

        self._rank_badge = RankBadge()
        right.addWidget(self._rank_badge)

        right.addWidget(self._mk_divider())

        self._level_lbl = QLabel("LVL 1")
        self._level_lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 15px; font-weight: bold;"
        )
        right.addWidget(self._level_lbl)

        self._prestige_lbl = QLabel("")
        self._prestige_lbl.setStyleSheet(
            f"color: {DANGER}; font-size: 9px; font-weight: bold; letter-spacing: 1px;"
        )
        self._prestige_lbl.hide()
        right.addWidget(self._prestige_lbl)

        self._gold_lbl = QLabel("GOLD: 0")
        self._gold_lbl.setObjectName("goldLabel")
        right.addWidget(self._gold_lbl)

        self._streak_lbl = QLabel("STREAK: 0")
        self._streak_lbl.setObjectName("streakLabel")
        right.addWidget(self._streak_lbl)

        self._best_lbl = QLabel("BEST: 0")
        self._best_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        right.addWidget(self._best_lbl)

        right.addWidget(self._mk_divider())

        # Theme toggle
        self._theme_btn = QPushButton("THEME: CYAN")
        self._theme_btn.setFixedWidth(110)
        self._theme_btn.setStyleSheet(
            f"color: {TEXT_MUTED}; border-color: {BORDER_DIM}; font-size: 9px; padding: 4px 8px;"
        )
        self._theme_btn.clicked.connect(self._toggle_theme)
        right.addWidget(self._theme_btn)

        lay.addLayout(right)
        return frame

    # ── EXP bar ──────────────────────────────────────────────────────────────

    def _mk_exp_row(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        exp_lbl = QLabel("EXP:")
        exp_lbl.setObjectName("accentLabel")
        exp_lbl.setFixedWidth(42)
        self._exp_bar = NeonExpBar()
        lay.addWidget(exp_lbl)
        lay.addWidget(self._exp_bar)
        return w

    # ── Navigation bar ────────────────────────────────────────────────────────

    def _mk_nav_bar(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(38)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._nav_btns: list[QPushButton] = []
        for i, label in enumerate(_NAV_LABELS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            lay.addWidget(btn)
            self._nav_btns.append(btn)

        lay.addStretch()
        self._nav_btns[0].setChecked(True)
        self._nav_btns[0].setStyleSheet(self._nav_btn_style(True))
        return w

    def _nav_btn_style(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton {{ background-color: {ACCENT_CYAN}; color: {BG_DARK}; "
                f"border: 1px solid {ACCENT_CYAN}; border-radius: 2px; "
                f"font-weight: bold; font-size: 10px; letter-spacing: 1px; padding: 0 10px; }}"
            )
        return (
            f"QPushButton {{ background-color: {BG_PANEL}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER_DIM}; border-radius: 2px; "
            f"font-size: 10px; letter-spacing: 1px; padding: 0 10px; }}"
            f"QPushButton:hover {{ color: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; }}"
        )

    def _switch_tab(self, idx: int) -> None:
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._nav_btn_style(i == idx))
        self._stack.setCurrentIndex(idx)
        self._on_tab_activated(idx)

    def _on_tab_activated(self, idx: int) -> None:
        if idx == _TAB_JOURNAL:
            self._journal.refresh()
        elif idx == _TAB_CALENDAR:
            self._calendar.refresh()
        elif idx == _TAB_STATS:
            self._stats.refresh()
        elif idx == _TAB_BADGES:
            self._achievements.refresh()
        elif idx == _TAB_SHOP:
            self._shop.refresh()
        elif idx == _TAB_TASKS:
            self._tasks.refresh()
        elif idx == _TAB_EXPLAIN:
            self._explain.refresh()
        elif idx == _TAB_TREE:
            self._skill_tree.refresh()
        elif idx == _TAB_SETTINGS:
            self._settings.refresh()

    # ── Content stack ─────────────────────────────────────────────────────────

    def _mk_content_stack(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._stack.addWidget(self._mk_quest_page())   # 0
        self._journal      = JournalPanel()            # 1
        self._calendar     = CalendarPanel()           # 2
        self._stats        = StatsPanel()              # 3
        self._achievements = AchievementsPanel()       # 4
        self._shop         = ShopPanel()               # 5
        self._shop.purchase_made.connect(self._refresh)
        self._tasks        = TaskEditorPanel()         # 6
        self._tasks.tasks_changed.connect(self._refresh)
        self._explain      = ExplainPanel()            # 7
        self._skill_tree   = SkillTreePanel()          # 8
        self._settings     = SettingsPanel()           # 9
        self._settings.particles_toggled.connect(self._on_particles_toggled)
        self._settings.prestige_performed.connect(self._on_prestige_done)
        for panel in (self._journal, self._calendar, self._stats,
                      self._achievements, self._shop, self._tasks,
                      self._explain, self._skill_tree, self._settings):
            self._stack.addWidget(panel)
        return self._stack

    # ── Quest page (index 0) ──────────────────────────────────────────────────

    def _mk_quest_page(self) -> QWidget:
        page = QWidget()
        lay  = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lay.addWidget(self._mk_quest_section())
        lay.addWidget(self._mk_sep())
        lay.addWidget(self._mk_pomodoro_section())
        lay.addWidget(self._mk_sep())
        lay.addWidget(self._mk_side_quest_section())
        lay.addWidget(self._mk_sep())
        lay.addWidget(self._mk_boss_section())
        lay.addWidget(self._mk_sep())
        lay.addWidget(self._mk_footer())
        lay.addWidget(self._mk_sep())
        lay.addWidget(self._mk_skill_section())
        return page

    # ── Quest section ─────────────────────────────────────────────────────────

    def _mk_quest_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        title = QLabel("[!]  DAILY QUEST: THE PATH TO S-RANK DV ENGINEER")
        title.setObjectName("questTitle")
        lay.addWidget(title)

        self._cards: dict[str, QuestCard] = {}
        for qtype in ("PROJECT", "THEORY", "SKILL"):
            card = QuestCard(qtype)
            card.completion_requested.connect(self._on_quest_requested)
            card.undo_requested.connect(self._on_quest_undo)
            lay.addWidget(card)
            self._cards[qtype] = card

        return w

    # ── Pomodoro section ──────────────────────────────────────────────────────

    def _mk_pomodoro_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("FOCUS TIMER")
        hdr_lbl.setObjectName("sectionHeader")
        self._pomo_toggle = QPushButton("▼ SHOW")
        self._pomo_toggle.setStyleSheet(
            f"color: {TEXT_MUTED}; border: none; font-size: 10px; "
            f"background: transparent; padding: 0;"
        )
        self._pomo_toggle.setFixedWidth(70)
        self._pomo_toggle.clicked.connect(self._toggle_pomodoro)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(self._pomo_toggle)
        lay.addLayout(hdr_row)

        self._pomo_frame = QWidget()
        self._pomodoro   = PomodoroWidget(self._pomo_frame)
        fl = QVBoxLayout(self._pomo_frame)
        fl.setContentsMargins(0, 2, 0, 2)
        fl.addWidget(self._pomodoro)
        self._pomodoro.session_completed.connect(self._on_pomodoro_done)
        self._pomo_frame.hide()
        lay.addWidget(self._pomo_frame)
        return w

    def _toggle_pomodoro(self):
        visible = self._pomo_frame.isVisible()
        self._pomo_frame.setVisible(not visible)
        self._pomo_toggle.setText("▲ HIDE" if not visible else "▼ SHOW")

    def _on_pomodoro_done(self, count: int):
        self._toast_mgr.show(
            "POMODORO COMPLETE!",
            f"Focus session done — {count} pomodoro(s) today  +EXP bonus!",
            "success",
        )

    # ── Side quest section ────────────────────────────────────────────────────

    def _mk_side_quest_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("SIDE QUESTS")
        hdr_lbl.setObjectName("sectionHeader")
        self._sq_toggle = QPushButton("▼ SHOW")
        self._sq_toggle.setStyleSheet(
            f"color: {TEXT_MUTED}; border: none; font-size: 10px; "
            f"background: transparent; padding: 0;"
        )
        self._sq_toggle.setFixedWidth(70)
        self._sq_toggle.clicked.connect(self._toggle_side_quests)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(self._sq_toggle)
        lay.addLayout(hdr_row)

        self._sq_frame = QWidget()
        self._sq_frame.hide()
        self._sq_inner = QVBoxLayout(self._sq_frame)
        self._sq_inner.setContentsMargins(0, 4, 0, 4)
        self._sq_inner.setSpacing(4)
        lay.addWidget(self._sq_frame)
        return w

    def _toggle_side_quests(self):
        visible = self._sq_frame.isVisible()
        self._sq_frame.setVisible(not visible)
        self._sq_toggle.setText("▲ HIDE" if not visible else "▼ SHOW")
        if not visible:
            self._refresh_side_quests()

    def _refresh_side_quests(self):
        from game_logic import get_daily_side_quests
        today = _date.today().isoformat()
        quests = get_daily_side_quests(today, 3)
        done   = db.get_side_quest_completions(today)

        # Clear existing rows
        while self._sq_inner.count():
            item = self._sq_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for q in quests:
            row    = QWidget()
            r_lay  = QHBoxLayout(row)
            r_lay.setContentsMargins(6, 4, 6, 4)
            r_lay.setSpacing(8)

            is_done = q["quest_key"] in done

            cat_colors = {"PROJECT": "#ff7700", "THEORY": "#00aaff",
                          "SKILL": "#bb44ff", "CUSTOM": ACCENT_CYAN}
            cat_lbl = QLabel(f"[{q['category']}]")
            cat_lbl.setFixedWidth(66)
            cat_lbl.setStyleSheet(
                f"color: {cat_colors.get(q['category'], ACCENT_CYAN)}; "
                f"font-size: 9px; font-weight: bold; background: transparent;"
            )
            r_lay.addWidget(cat_lbl)

            name_lbl = QLabel(q["name"])
            name_lbl.setStyleSheet(
                f"color: {'#446644' if is_done else TEXT_PRIMARY}; "
                f"font-size: 10px; background: transparent;"
            )
            r_lay.addWidget(name_lbl)
            r_lay.addStretch()

            rwd_lbl = QLabel(f"+{q['exp']} EXP  +{q['gold']} G")
            rwd_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;")
            r_lay.addWidget(rwd_lbl)

            if is_done:
                done_lbl = QLabel("✔ DONE")
                done_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 9px; background: transparent;")
                r_lay.addWidget(done_lbl)
            else:
                btn = QPushButton("COMPLETE")
                btn.setFixedWidth(80)
                btn.setStyleSheet(
                    f"color: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; font-size: 9px; padding: 2px 6px;"
                )
                btn.clicked.connect(lambda _, sq=q: self._on_side_quest_complete(sq))
                r_lay.addWidget(btn)

            self._sq_inner.addWidget(row)

    def _on_side_quest_complete(self, quest: dict):
        today  = _date.today().isoformat()
        result = db.complete_side_quest(
            quest["quest_key"], today, quest["name"], quest["exp"], quest["gold"]
        )
        if result.get("success"):
            self._toast_mgr.show(
                "SIDE QUEST COMPLETE!",
                f"{quest['name'][:45]}  +{quest['exp']} EXP  +{quest['gold']} G",
                "success",
            )
            if result.get("leveled"):
                old_rank, _ = game_logic.get_rank_info(result["old_level"])
                new_rank, new_title = game_logic.get_rank_info(result["new_level"])
                QTimer.singleShot(400, lambda: self._show_levelup(
                    result["old_level"], result["new_level"],
                    old_rank, new_rank, quest["exp"], quest["gold"],
                ))
            self._refresh()
            self._refresh_side_quests()

    # ── Boss battle section ───────────────────────────────────────────────────

    def _mk_boss_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("BOSS BATTLE")
        hdr_lbl.setObjectName("sectionHeader")
        self._boss_toggle = QPushButton("▼ SHOW")
        self._boss_toggle.setStyleSheet(
            f"color: {TEXT_MUTED}; border: none; font-size: 10px; "
            f"background: transparent; padding: 0;"
        )
        self._boss_toggle.setFixedWidth(70)
        self._boss_toggle.clicked.connect(self._toggle_boss)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(self._boss_toggle)
        lay.addLayout(hdr_row)

        self._boss_frame = QWidget()
        boss_inner = QVBoxLayout(self._boss_frame)
        boss_inner.setContentsMargins(0, 4, 0, 4)
        boss_inner.setSpacing(6)

        self._boss_status_lbl = QLabel("")
        self._boss_status_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px;"
        )
        boss_inner.addWidget(self._boss_status_lbl)

        self._boss_btn = QPushButton("⚔  ENGAGE BOSS BATTLE  ⚔")
        self._boss_btn.setObjectName("warnBtn")
        self._boss_btn.setFixedHeight(44)
        self._boss_btn.clicked.connect(self._on_boss_complete)
        boss_inner.addWidget(self._boss_btn)

        self._boss_hint_lbl = QLabel("")
        self._boss_hint_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px;"
        )
        boss_inner.addWidget(self._boss_hint_lbl)

        self._boss_frame.hide()
        lay.addWidget(self._boss_frame)
        return w

    def _toggle_boss(self) -> None:
        visible = self._boss_frame.isVisible()
        self._boss_frame.setVisible(not visible)
        self._boss_toggle.setText("▲ HIDE" if not visible else "▼ SHOW")

    # ── Footer (week strip + audio) ───────────────────────────────────────────

    def _mk_footer(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        # Week strip
        week_col = QVBoxLayout()
        week_col.setSpacing(2)
        wk_hdr = QLabel("WEEK")
        wk_hdr.setObjectName("sectionHeader")
        self._week_strip = WeekStrip()
        week_col.addWidget(wk_hdr)
        week_col.addWidget(self._week_strip)
        bottom_row.addLayout(week_col)
        bottom_row.addStretch()

        # Audio controls
        audio_col = QVBoxLayout()
        audio_col.setSpacing(4)
        audio_col.setAlignment(Qt.AlignRight)

        self._track_lbl = QLabel("SOUNDTRACK: —")
        self._track_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        self._track_lbl.setAlignment(Qt.AlignRight)
        audio_col.addWidget(self._track_lbl)

        vol_row = QHBoxLayout()
        vol_row.setSpacing(8)
        vol_lbl = QLabel("VOL")
        vol_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(70)
        self._vol_slider.setFixedWidth(120)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        self._mute_btn = QPushButton("MUTE")
        self._mute_btn.setObjectName("muteBtn")
        self._mute_btn.setCheckable(True)
        self._mute_btn.setFixedWidth(60)
        self._mute_btn.clicked.connect(self._on_mute_toggled)
        vol_row.addWidget(vol_lbl)
        vol_row.addWidget(self._vol_slider)
        vol_row.addWidget(self._mute_btn)
        audio_col.addLayout(vol_row)

        bottom_row.addLayout(audio_col)
        lay.addLayout(bottom_row)

        self._dev_hint = QLabel("[ CTRL+SHIFT+D → DEV MODE ]")
        self._dev_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        self._dev_hint.setAlignment(Qt.AlignRight)
        lay.addWidget(self._dev_hint)

        return w

    # ── Skill section ─────────────────────────────────────────────────────────

    def _mk_skill_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("SKILL MATRIX")
        hdr_lbl.setObjectName("sectionHeader")
        self._skill_toggle = QPushButton("▼ SHOW")
        self._skill_toggle.setStyleSheet(
            f"color: {TEXT_MUTED}; border: none; font-size: 10px; "
            f"background: transparent; padding: 0;"
        )
        self._skill_toggle.setFixedWidth(70)
        self._skill_toggle.clicked.connect(self._toggle_skill_table)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(self._skill_toggle)
        lay.addLayout(hdr_row)

        frame = QWidget()
        frame.setObjectName("skillFrame")
        frame.setStyleSheet(
            f"QWidget#skillFrame {{"
            f"  background: {BG_PANEL};"
            f"  border: 1px solid #152035;"
            f"  border-radius: 3px;"
            f"}}"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        self._skill_table = SkillTable()
        self._skill_table.setFixedHeight(220)
        fl.addWidget(self._skill_table)

        self._skill_frame = frame
        self._skill_frame.hide()
        lay.addWidget(self._skill_frame)
        return w

    def _toggle_skill_table(self) -> None:
        visible = self._skill_frame.isVisible()
        self._skill_frame.setVisible(not visible)
        self._skill_toggle.setText("▲ HIDE" if not visible else "▼ SHOW")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _mk_sep() -> QWidget:
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {ACCENT_CYAN};")
        return line

    @staticmethod
    def _mk_divider() -> QLabel:
        d = QLabel("|")
        d.setStyleSheet(f"color: {TEXT_MUTED};")
        return d

    # ═══════════════════════════════════════════════════════════════════════
    # Overlays
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_overlays(self):
        self._levelup_ov  = LevelUpOverlay(self)
        self._rankup_ov   = RankUpOverlay(self)
        self._prestige_ov = PrestigeOverlay(self)
        self._penalty_ov  = PenaltyZoneWidget(self)
        self._toast_mgr   = ToastManager(self)
        self._penalty_ov.cleared.connect(self._exit_penalty_mode)

        # Particle background (placed behind content via stacking)
        self._particles = ParticleBg(self)
        self._particles.lower()
        particles_on = db.get_setting("particles_enabled", "1") == "1"
        self._particles.set_enabled(particles_on)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        for ov in (self._levelup_ov, self._rankup_ov, self._prestige_ov, self._penalty_ov):
            if ov.isVisible():
                ov.setGeometry(self.rect())
        self._particles.setGeometry(self.rect())
        self._toast_mgr.reposition()

    # ═══════════════════════════════════════════════════════════════════════
    # Shortcuts + timers
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_shortcuts(self):
        sc = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        sc.activated.connect(self._toggle_dev_panel)

    def _setup_timers(self):
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start(60_000)

        # Daily reminder check (every 5 min)
        self._reminder_timer = QTimer(self)
        self._reminder_timer.timeout.connect(self._check_reminder)
        self._reminder_timer.start(300_000)

    def _on_tick(self):
        self._check_rollover()
        self._refresh()

    # ═══════════════════════════════════════════════════════════════════════
    # System tray
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_make_tray_icon())
        self._tray.setToolTip("Hunter's System Interface")

        menu = QMenu()
        show_action = menu.addAction("Show Window")
        show_action.triggered.connect(self._tray_show)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        self._tray.setContextMenu(menu)

        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _tray_show(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._tray_show()

    def closeEvent(self, event) -> None:
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Hunter's System Interface",
            "Running in background. Click the tray icon to restore.",
            QSystemTrayIcon.Information,
            2000,
        )

    def _check_reminder(self) -> None:
        if db.get_setting("reminder_enabled", "1") != "1":
            return
        try:
            reminder_hour = int(db.get_setting("reminder_hour", "20"))
        except ValueError:
            reminder_hour = 20

        now = datetime.now()
        if now.hour != reminder_hour or now.minute > 5:
            return

        today = date_helper.get_today_str()
        log   = db.get_quest_log(today)
        if not log:
            return
        all_done = (log.get("project_completed") and
                    log.get("theory_completed")  and
                    log.get("skill_completed"))
        if not all_done:
            self._tray.showMessage(
                "HUNTER'S SYSTEM — QUEST REMINDER",
                "Daily quests are not yet complete! Don't break your streak.",
                QSystemTrayIcon.Warning,
                5000,
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Theme
    # ═══════════════════════════════════════════════════════════════════════

    def _toggle_theme(self) -> None:
        self._current_theme = "red" if self._current_theme == "cyan" else "cyan"
        db.set_setting("theme", self._current_theme)
        self.setStyleSheet(get_stylesheet(self._current_theme))
        label = "THEME: RED" if self._current_theme == "red" else "THEME: CYAN"
        self._theme_btn.setText(label)
        self._toast_mgr.show("THEME CHANGED", f"Now using {self._current_theme.upper()} theme", "info")

    # ═══════════════════════════════════════════════════════════════════════
    # Dev panel
    # ═══════════════════════════════════════════════════════════════════════

    def _open_dev_panel(self):
        if self._dev_panel is None:
            from ui.dev_panel import DevPanel
            self._dev_panel = DevPanel(self)
            self._dev_panel.refresh_requested.connect(self._on_dev_refresh)
        self._dev_panel.show()
        self._dev_panel.raise_()

    def _toggle_dev_panel(self):
        if self._dev_panel is None or not self._dev_panel.isVisible():
            self._open_dev_panel()
        else:
            self._dev_panel.hide()

    def _on_dev_refresh(self):
        self._check_rollover()
        self._refresh()

    # ═══════════════════════════════════════════════════════════════════════
    # Rollover / penalty
    # ═══════════════════════════════════════════════════════════════════════

    def _check_rollover(self):
        today      = date_helper.get_today_str()
        last_reset = db.get_setting("last_reset_date")

        if today == last_reset:
            self._check_penalty_state()
            return

        today_date = date_helper.get_today()
        yesterday  = (today_date - timedelta(days=1)).isoformat()
        y_log      = db.get_quest_log(yesterday)

        if y_log:
            all_done = (y_log.get("project_completed") and
                        y_log.get("theory_completed")  and
                        y_log.get("skill_completed"))
            hunter = db.get_hunter()
            if all_done:
                new_streak = hunter["streak"] + 1
                new_best   = max(hunter["best_streak"], new_streak)
                db.update_hunter(streak=new_streak, best_streak=new_best)
            else:
                # Check for streak shield
                if db.get_setting("streak_shield", "0") == "1":
                    db.set_setting("streak_shield", "0")
                    self._toast_mgr.show(
                        "STREAK SHIELD USED",
                        "Your streak was protected by the Streak Shield!",
                        "warn",
                    )
                else:
                    db.update_quest_log(yesterday, penalty_triggered=1)
                    db.update_hunter(streak=0)
                    existing = db.get_setting("penalty_deadline")
                    if not existing:
                        deadline = (datetime.now(timezone.utc) + timedelta(seconds=2700)).isoformat()
                        db.set_setting("penalty_deadline", deadline)

        db.get_or_create_quest_log(today)
        db.set_setting("last_reset_date", today)
        self._check_penalty_state()
        self._check_boss_unlock()

    def _check_penalty_state(self):
        deadline_str = db.get_setting("penalty_deadline")
        if not deadline_str:
            return
        try:
            deadline = datetime.fromisoformat(deadline_str)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
        except ValueError:
            db.set_setting("penalty_deadline", "")
            return
        if remaining <= 0:
            db.set_setting("penalty_deadline", "")
            return
        self._enter_penalty_mode(remaining)

    def _enter_penalty_mode(self, remaining_secs: float):
        if self._penalty_ov.isVisible():
            return
        self._penalty_ov.setGeometry(self.rect())
        self._penalty_ov.start(remaining_secs)
        self._audio.set_state("penalty")

    def _exit_penalty_mode(self):
        db.set_setting("penalty_deadline", "")
        self._penalty_ov.stop()
        self._audio.set_state("idle")
        self._refresh()
        self._toast_mgr.show("PENALTY COMPLETE", "System unlocked — continue your quest.", "success")

    # ═══════════════════════════════════════════════════════════════════════
    # Boss battle
    # ═══════════════════════════════════════════════════════════════════════

    def _check_boss_unlock(self) -> None:
        if db.check_boss_unlock():
            self._toast_mgr.show(
                "BOSS BATTLE UNLOCKED!",
                "A powerful enemy has appeared — 5-day streak achieved!",
                "warn",
                timeout=5000,
            )

    def _on_boss_complete(self) -> None:
        result = db.complete_boss_battle()
        if not result.get("success"):
            self._toast_mgr.show("BOSS", result.get("message", "Failed"), "danger")
            return

        self._audio.play_chime("combo")
        self._toast_mgr.show(
            "BOSS DEFEATED!",
            f"+{result['exp_awarded']} EXP  +{result['gold_awarded']} GOLD",
            "combo",
            timeout=5000,
        )

        hunter = db.get_hunter()
        skills = db.get_all_skills()
        newly  = db.check_and_unlock_achievements(hunter, skills)
        self._notify_achievements(newly)

        if result.get("leveled"):
            old_rank, _ = game_logic.get_rank_info(result["old_level"])
            new_rank, new_title = game_logic.get_rank_info(result["new_level"])
            QTimer.singleShot(400, lambda: self._show_levelup(
                result["old_level"], result["new_level"], old_rank, new_rank,
                result["exp_awarded"], result["gold_awarded"],
            ))
            if new_rank != old_rank:
                QTimer.singleShot(5000, lambda: self._show_rankup(old_rank, new_rank, result["new_level"], new_title))

        self._refresh()

    # ═══════════════════════════════════════════════════════════════════════
    # Quest completion
    # ═══════════════════════════════════════════════════════════════════════

    def _on_quest_requested(self, quest_type: str, skill_name: str):
        today = date_helper.get_today_str()
        log   = db.get_quest_log(today)
        if not log:
            return

        col_map = {"PROJECT": "project_completed", "THEORY": "theory_completed",
                   "SKILL": "skill_completed"}
        if log.get(col_map.get(quest_type, ""), 0):
            return

        update_kw: dict = {col_map[quest_type]: 1}
        if quest_type == "SKILL" and skill_name:
            update_kw["skill_name"] = skill_name
        db.update_quest_log(today, **update_kw)

        # Credit skill
        if quest_type == "SKILL" and skill_name:
            skills = {s["skill_name"]: s for s in db.get_all_skills()}
            if skill_name in skills:
                old_pts  = skills[skill_name]["proficiency_points"]
                new_pts  = old_pts + 10
                new_rank = game_logic.get_skill_rank(new_pts)
                db.update_skill(skill_name, proficiency_points=new_pts, current_rank=new_rank)
                if new_rank != skills[skill_name]["current_rank"]:
                    self._toast_mgr.show(
                        f"{skill_name} RANK UP!",
                        f"{skills[skill_name]['current_rank']} → {new_rank}  ({new_pts} pts)",
                        "success",
                    )

        # EXP / Gold — apply active boosts
        boosts    = db.get_active_boosts()
        exp_mult  = 2 if "exp_boost"  in boosts else 1
        gold_mult = 2 if "gold_boost" in boosts else 1
        exp_gain  = game_logic.EXP_TABLE[quest_type]  * exp_mult
        gold_gain = game_logic.GOLD_TABLE[quest_type] * gold_mult

        # Combo check
        fresh_log = db.get_quest_log(today)
        all_done  = (fresh_log.get("project_completed") and
                     fresh_log.get("theory_completed")  and
                     fresh_log.get("skill_completed"))
        if all_done:
            exp_gain  += game_logic.EXP_TABLE["COMBO"]  * exp_mult
            gold_gain += game_logic.GOLD_TABLE["COMBO"] * gold_mult

        old_awarded = fresh_log.get("exp_awarded", 0)
        db.update_quest_log(today, exp_awarded=old_awarded + exp_gain)

        # Level-up
        hunter    = db.get_hunter()
        old_level = hunter["level"]
        old_rank, old_rank_title = game_logic.get_rank_info(old_level)

        new_lvl, new_exp, new_next = game_logic.apply_exp_gain(
            old_level, hunter["current_exp"], exp_gain
        )
        new_rank, new_title = game_logic.get_rank_info(new_lvl)

        db.update_hunter(
            level         = new_lvl,
            current_exp   = new_exp,
            next_level_exp= new_next,
            gold          = hunter["gold"] + gold_gain,
            title         = new_title,
        )

        # Streak update on combo
        if all_done:
            h2         = db.get_hunter()
            new_streak = h2["streak"] + 1
            new_best   = max(h2["best_streak"], new_streak)
            db.update_hunter(streak=new_streak, best_streak=new_best)
            self._check_boss_unlock()

        # Animate card
        self._cards[quest_type].animate_completion()

        # Audio
        self._audio.play_chime("clear")
        if new_lvl > old_level:
            self._audio.play_chime("levelup")
        if all_done:
            self._audio.play_chime("combo")
        self._audio.set_state("idle" if all_done else "questing")

        # Level-up overlay
        if new_lvl > old_level:
            QTimer.singleShot(400, lambda: self._show_levelup(
                old_level, new_lvl, old_rank, new_rank, exp_gain, gold_gain,
            ))

        # Rank-up overlay (fires after level-up overlay fades)
        if new_rank != old_rank:
            QTimer.singleShot(5200, lambda: self._show_rankup(
                old_rank, new_rank, new_lvl, new_title
            ))

        # Combo toast
        if all_done:
            self._toast_mgr.show(
                "ALL QUESTS CLEARED! ⚡",
                f"COMBO BONUS  +{game_logic.EXP_TABLE['COMBO']} EXP  "
                f"+{game_logic.GOLD_TABLE['COMBO']} GOLD",
                "combo",
                timeout=4500,
            )
        else:
            boost_tag = "  [BOOSTED]" if exp_mult > 1 else ""
            self._toast_mgr.show(
                f"{quest_type} COMPLETE{boost_tag}",
                f"+{game_logic.EXP_TABLE[quest_type] * exp_mult} EXP  "
                f"+{game_logic.GOLD_TABLE[quest_type] * gold_mult} GOLD",
                "success",
            )

        # Achievement checks
        final_hunter = db.get_hunter()
        final_skills = db.get_all_skills()
        newly = db.check_and_unlock_achievements(final_hunter, final_skills, combo_today=all_done)
        self._notify_achievements(newly)

        self._refresh()

    def _on_quest_undo(self, quest_type: str):
        today  = date_helper.get_today_str()
        result = db.uncomplete_quest_log(quest_type, today)
        if result.get("success"):
            self._toast_mgr.show(
                f"{quest_type} UNDONE",
                "Quest marked incomplete — EXP and Gold reversed.",
                "warn",
            )
            self._refresh()

    def _notify_achievements(self, achievement_ids: list) -> None:
        from game_logic import ACHIEVEMENTS
        ach_map = {a["id"]: a for a in ACHIEVEMENTS}
        for aid in achievement_ids:
            a = ach_map.get(aid)
            if a:
                self._toast_mgr.show(
                    f"ACHIEVEMENT UNLOCKED: {a['name']}",
                    a["desc"],
                    "combo",
                    timeout=5000,
                )

    # ═══════════════════════════════════════════════════════════════════════
    # Overlay helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _show_levelup(self, old_lvl, new_lvl, old_rank, new_rank, exp, gold):
        self._levelup_ov.setGeometry(self.rect())
        self._levelup_ov.show_levelup(old_lvl, new_lvl, old_rank, new_rank, exp, gold)

    def _show_rankup(self, old_rank, new_rank, new_level, new_title):
        self._rankup_ov.setGeometry(self.rect())
        self._rankup_ov.show_rankup(old_rank, new_rank, new_level, new_title)

    def _on_prestige_done(self, result: dict):
        from game_logic import get_prestige_title
        self._prestige_ov.setGeometry(self.rect())
        self._prestige_ov.show_prestige(
            result["prestige_num"],
            result.get("title", get_prestige_title(result["prestige_num"])),
            result["old_level"],
            result["gold_kept"],
        )
        self._audio.play_chime("levelup")
        self._refresh()
        hunter = db.get_hunter()
        skills = db.get_all_skills()
        newly  = db.check_and_unlock_achievements(hunter, skills)
        self._notify_achievements(newly)

    def _on_particles_toggled(self, enabled: bool):
        self._particles.set_enabled(enabled)

    # ═══════════════════════════════════════════════════════════════════════
    # Audio controls
    # ═══════════════════════════════════════════════════════════════════════

    def _on_volume_changed(self, value: int):
        vol = value / 100.0
        self._audio.set_volume(vol)
        db.set_setting("volume", str(vol))

    def _on_mute_toggled(self, checked: bool):
        self._audio.set_muted(checked)
        db.set_setting("muted", "1" if checked else "0")
        self._mute_btn.setText("UNMUTE" if checked else "MUTE")

    # ═══════════════════════════════════════════════════════════════════════
    # Data refresh
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh(self):
        today  = date_helper.get_today_str()
        hunter = db.get_hunter()
        log    = db.get_or_create_quest_log(today)

        if not hunter:
            return

        level    = hunter["level"]
        exp      = hunter["current_exp"]
        next_exp = hunter["next_level_exp"]
        gold     = hunter["gold"]
        streak   = hunter["streak"]
        best     = hunter["best_streak"]
        rank, _  = game_logic.get_rank_info(level)

        prestige = hunter.get("prestige_count", 0)
        self._rank_badge.set_rank(rank)
        self._level_lbl.setText(f"LVL {level}")
        if prestige and prestige > 0:
            self._prestige_lbl.setText(f"PRESTIGE {prestige}")
            self._prestige_lbl.show()
        else:
            self._prestige_lbl.hide()
        self._gold_lbl.setText(f"GOLD: {gold:,}")
        streak_icon = " 🔥" if streak >= 3 else ""
        self._streak_lbl.setText(f"STREAK: {streak}{streak_icon}")
        self._best_lbl.setText(f"BEST: {best}")

        all_done = (log.get("project_completed") and
                    log.get("theory_completed") and
                    log.get("skill_completed"))
        self._status_lbl.setText(
            "STATUS: DUNGEON CLEARED ✔" if all_done else "STATUS: ACTIVE"
        )
        self._status_lbl.style().unpolish(self._status_lbl)
        self._status_lbl.style().polish(self._status_lbl)

        self._exp_bar.set_progress(exp, next_exp, animate=True)

        for qtype, col in [("PROJECT", "project_completed"),
                            ("THEORY",  "theory_completed"),
                            ("SKILL",   "skill_completed")]:
            self._cards[qtype].set_completed(bool(log.get(col, 0)))

        # Week strip
        today_date = date_helper.get_today()
        mon  = today_date - timedelta(days=today_date.weekday())
        sun  = mon + timedelta(days=6)
        logs = {r["date"]: r for r in db.get_quest_logs_range(
            mon.isoformat(), sun.isoformat()
        )}
        self._week_strip.refresh(today, logs)

        # Skill table
        self._skill_table.refresh(db.get_all_skills())

        # Boss section
        self._refresh_boss()

        # Audio
        vol   = float(db.get_setting("volume", "0.70"))
        muted = db.get_setting("muted", "0") == "1"
        self._vol_slider.blockSignals(True)
        self._vol_slider.setValue(int(vol * 100))
        self._vol_slider.blockSignals(False)
        self._mute_btn.setChecked(muted)
        self._mute_btn.setText("UNMUTE" if muted else "MUTE")
        self._audio.set_volume(vol)
        self._audio.set_muted(muted)
        self._update_track_label()

        # Dev hint
        if date_helper.is_simulated():
            self._dev_hint.setText(f"[ DEV DATE: {today} | CTRL+SHIFT+D ]")
            self._dev_hint.setStyleSheet(f"color: {WARNING}; font-size: 10px;")
        else:
            self._dev_hint.setText("[ CTRL+SHIFT+D → DEV MODE ]")
            self._dev_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")

        # Theme button label
        label = "THEME: RED" if self._current_theme == "red" else "THEME: CYAN"
        self._theme_btn.setText(label)

    def _refresh_boss(self) -> None:
        boss = db.get_boss_status()
        week = boss.get("week", "")
        if not boss.get("unlocked"):
            hunter = db.get_hunter()
            streak = hunter.get("streak", 0)
            needed = max(0, 5 - streak)
            self._boss_status_lbl.setText(
                f"LOCKED  —  Reach a 5-day streak to unlock this week's boss"
                f"  ({streak}/5 days)"
            )
            self._boss_btn.setEnabled(False)
            self._boss_hint_lbl.setText(f"Current week: {week}  |  {needed} more day(s) needed")
        elif boss.get("completed"):
            self._boss_status_lbl.setText(
                f"CLEARED THIS WEEK  ✔  +{boss.get('exp_awarded', 200)} EXP awarded"
            )
            self._boss_status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px;")
            self._boss_btn.setEnabled(False)
            self._boss_hint_lbl.setText(f"Completed: {boss.get('completed_date', '')}")
        else:
            self._boss_status_lbl.setText("BOSS BATTLE AVAILABLE  —  +200 EXP  +100 GOLD")
            self._boss_status_lbl.setStyleSheet(f"color: {WARNING}; font-size: 11px;")
            self._boss_btn.setEnabled(True)
            self._boss_hint_lbl.setText("Complete the boss battle to earn bonus EXP and GOLD")

    def _update_track_label(self):
        labels = {
            "idle":     "Awakening (idle loop)",
            "questing": "Battle Theme (active)",
            "penalty":  "Penalty Zone (ticking)",
            "":         "—  (no audio files found)",
        }
        state = self._audio._state if self._audio.available else ""
        self._track_lbl.setText(f"SOUNDTRACK: {labels.get(state, '—')}")
