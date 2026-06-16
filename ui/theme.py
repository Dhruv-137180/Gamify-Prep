"""Color palette, animation constants, and QSS stylesheet."""

# ── Palette (Cyan / default theme) ────────────────────────────────────────────
BG_DARK        = "#080d18"
BG_PANEL       = "#0c1322"
BG_CARD        = "#0f1a2e"
BG_HOVER       = "#13203a"
ACCENT_CYAN    = "#00d4ff"
ACCENT_BLUE    = "#0055cc"
ACCENT_DEEP    = "#002277"
TEXT_PRIMARY   = "#deeeff"
TEXT_SECONDARY = "#4a6a8a"
TEXT_MUTED     = "#1e3050"
SUCCESS        = "#00e87a"
SUCCESS_DIM    = "#00aa55"
WARNING        = "#ffaa00"
DANGER         = "#ff2244"
GOLD           = "#ffd700"
GOLD_DIM       = "#aa8800"
BORDER_DIM     = "#152035"
BORDER_BRIGHT  = "#0088bb"

# ── Rank colours ──────────────────────────────────────────────────────────────
RANK_COLORS = {
    "E-RANK": ACCENT_CYAN,
    "D-RANK": ACCENT_CYAN,
    "C-RANK": "#00ff88",
    "B-RANK": "#ffaa00",
    "A-RANK": "#ff6600",
    "S-RANK": "#ffd700",
}

# ── Penalty zone ──────────────────────────────────────────────────────────────
PENALTY_BG     = "#0e0004"
PENALTY_PANEL  = "#180008"
PENALTY_ACCENT = "#ff2244"
PENALTY_DIM    = "#660011"
PENALTY_BORDER = "#880018"

# ── Animation constants ───────────────────────────────────────────────────────
ANIM_FAST   = 200    # ms
ANIM_MED    = 500    # ms
ANIM_SLOW   = 900    # ms
ANIM_XSLOW  = 1400   # ms

# ── Font stack ────────────────────────────────────────────────────────────────
FONT = '"Consolas", "Courier New", "Lucida Console", monospace'

# ── Main QSS ─────────────────────────────────────────────────────────────────
STYLESHEET = f"""
/* ── Base ── */
QMainWindow, QDialog, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT};
    font-size: 12px;
}}
QFrame {{ background-color: transparent; border: none; }}

/* ── Labels ── */
QLabel {{ color: {TEXT_PRIMARY}; background-color: transparent; }}
QLabel#accentLabel  {{ color: {ACCENT_CYAN}; font-weight: bold; letter-spacing: 1px; }}
QLabel#goldLabel    {{ color: {GOLD};    font-size: 12px; }}
QLabel#streakLabel  {{ color: {WARNING}; font-size: 12px; font-weight: bold; }}
QLabel#mutedLabel   {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
QLabel#questTitle   {{
    color: {ACCENT_CYAN};
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 4px 0;
}}
QLabel#sectionHeader {{
    color: {TEXT_SECONDARY};
    font-size: 10px;
    letter-spacing: 3px;
    padding: 2px 0;
}}
QLabel#statusOK     {{ color: {SUCCESS}; font-weight: bold; letter-spacing: 2px; font-size: 11px; }}
QLabel#statusBad    {{ color: {DANGER};  font-weight: bold; letter-spacing: 2px; font-size: 11px; }}

/* ── Frames ── */
QFrame#headerFrame {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_BRIGHT};
    border-radius: 3px;
}}
QFrame#skillFrame {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_DIM};
    border-radius: 3px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {BG_PANEL};
    color: {ACCENT_CYAN};
    border: 1px solid {BORDER_BRIGHT};
    border-radius: 2px;
    padding: 6px 16px;
    font-family: {FONT};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton:hover  {{ background-color: {ACCENT_BLUE}; color: {TEXT_PRIMARY}; border-color: {ACCENT_CYAN}; }}
QPushButton:pressed {{ background-color: {ACCENT_CYAN}; color: {BG_DARK}; }}
QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER_DIM}; }}
QPushButton#dangerBtn {{ color: {DANGER}; border-color: {DANGER}; }}
QPushButton#dangerBtn:hover {{ background-color: {DANGER}; color: {TEXT_PRIMARY}; }}
QPushButton#warnBtn {{ color: {WARNING}; border-color: {WARNING}; }}
QPushButton#warnBtn:hover {{ background-color: {WARNING}; color: {BG_DARK}; }}
QPushButton#muteBtn {{ min-width: 60px; padding: 4px 8px; font-size: 10px; }}

/* ── Checkboxes ── */
QCheckBox {{ color: {TEXT_PRIMARY}; spacing: 10px; font-size: 12px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {BORDER_BRIGHT};
    background-color: {BG_CARD};
    border-radius: 2px;
}}
QCheckBox::indicator:checked  {{ background-color: {SUCCESS}; border-color: {SUCCESS}; }}
QCheckBox::indicator:hover    {{ border-color: {ACCENT_CYAN}; }}
QCheckBox:disabled            {{ color: {TEXT_MUTED}; }}
QCheckBox::indicator:disabled {{ border-color: {BORDER_DIM}; }}

/* ── ComboBox ── */
QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_BRIGHT};
    border-radius: 2px;
    padding: 3px 8px;
    font-family: {FONT};
    font-size: 11px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {ACCENT_CYAN};
    width: 0; height: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_BRIGHT};
    selection-background-color: {ACCENT_BLUE};
    font-family: {FONT};
}}
QComboBox:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER_DIM}; }}

/* ── Inputs ── */
QLineEdit, QSpinBox, QDateEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_BRIGHT};
    border-radius: 2px;
    padding: 4px 8px;
    font-family: {FONT};
    font-size: 12px;
}}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {{ border-color: {ACCENT_CYAN}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDateEdit::up-button, QDateEdit::down-button {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_DIM};
    width: 16px;
}}

/* ── Volume slider ── */
QSlider::groove:horizontal {{
    background: {BG_CARD}; border: 1px solid {BORDER_DIM};
    height: 4px; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{ background: {ACCENT_BLUE}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {ACCENT_CYAN}; border: 1px solid {ACCENT_CYAN};
    width: 12px; height: 12px; margin: -4px 0; border-radius: 6px;
}}

/* ── GroupBox ── */
QGroupBox {{
    color: {ACCENT_CYAN};
    border: 1px solid {BORDER_BRIGHT};
    border-radius: 3px;
    margin-top: 12px;
    padding: 10px 8px 8px 8px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px; padding: 0 6px;
}}

/* ── ScrollBar ── */
QScrollBar:vertical {{ background: {BG_DARK}; width: 6px; border: none; }}
QScrollBar::handle:vertical {{
    background: {BORDER_BRIGHT}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {BG_DARK}; height: 6px; border: none; }}
QScrollBar::handle:horizontal {{
    background: {BORDER_BRIGHT}; border-radius: 3px; min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── ScrollArea ── */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ── Tooltip ── */
QToolTip {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_CYAN};
    font-family: {FONT};
    font-size: 11px;
    padding: 4px;
}}

/* ── Calendar ── */
QCalendarWidget QToolButton  {{ color: {ACCENT_CYAN}; background: {BG_PANEL}; }}
QCalendarWidget QAbstractItemView:enabled {{
    background: {BG_CARD}; color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_BLUE};
}}
"""

# ── Red / Crimson theme ───────────────────────────────────────────────────────
_R_BG_DARK        = "#110004"
_R_BG_PANEL       = "#1a0008"
_R_BG_CARD        = "#200010"
_R_ACCENT         = "#ff2244"
_R_ACCENT_BLUE    = "#aa0022"
_R_TEXT_PRIMARY   = "#ffe8ec"
_R_TEXT_SECONDARY = "#7a3040"
_R_TEXT_MUTED     = "#3a0815"
_R_BORDER_DIM     = "#3a0815"
_R_BORDER_BRIGHT  = "#880022"

STYLESHEET_RED = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {_R_BG_DARK};
    color: {_R_TEXT_PRIMARY};
    font-family: {FONT};
    font-size: 12px;
}}
QFrame {{ background-color: transparent; border: none; }}
QLabel {{ color: {_R_TEXT_PRIMARY}; background-color: transparent; }}
QLabel#accentLabel  {{ color: {_R_ACCENT}; font-weight: bold; letter-spacing: 1px; }}
QLabel#goldLabel    {{ color: {GOLD};       font-size: 12px; }}
QLabel#streakLabel  {{ color: {WARNING};    font-size: 12px; font-weight: bold; }}
QLabel#mutedLabel   {{ color: {_R_TEXT_SECONDARY}; font-size: 11px; }}
QLabel#questTitle   {{
    color: {_R_ACCENT};
    font-size: 13px; font-weight: bold; letter-spacing: 2px; padding: 4px 0;
}}
QLabel#sectionHeader {{
    color: {_R_TEXT_SECONDARY};
    font-size: 10px; letter-spacing: 3px; padding: 2px 0;
}}
QLabel#statusOK  {{ color: {SUCCESS}; font-weight: bold; letter-spacing: 2px; font-size: 11px; }}
QLabel#statusBad {{ color: {_R_ACCENT};  font-weight: bold; letter-spacing: 2px; font-size: 11px; }}
QFrame#headerFrame {{
    background-color: {_R_BG_PANEL};
    border: 1px solid {_R_BORDER_BRIGHT}; border-radius: 3px;
}}
QPushButton {{
    background-color: {_R_BG_PANEL};
    color: {_R_ACCENT};
    border: 1px solid {_R_BORDER_BRIGHT};
    border-radius: 2px; padding: 6px 16px;
    font-family: {FONT}; font-size: 11px; font-weight: bold; letter-spacing: 1px;
}}
QPushButton:hover  {{ background-color: {_R_ACCENT_BLUE}; color: {_R_TEXT_PRIMARY}; border-color: {_R_ACCENT}; }}
QPushButton:pressed {{ background-color: {_R_ACCENT}; color: #000; }}
QPushButton:disabled {{ color: {_R_TEXT_MUTED}; border-color: {_R_BORDER_DIM}; }}
QPushButton#dangerBtn {{ color: {_R_ACCENT}; border-color: {_R_ACCENT}; }}
QPushButton#dangerBtn:hover {{ background-color: {_R_ACCENT}; color: {_R_TEXT_PRIMARY}; }}
QPushButton#warnBtn {{ color: {WARNING}; border-color: {WARNING}; }}
QPushButton#warnBtn:hover {{ background-color: {WARNING}; color: {_R_BG_DARK}; }}
QPushButton#muteBtn {{ min-width: 60px; padding: 4px 8px; font-size: 10px; }}
QCheckBox {{ color: {_R_TEXT_PRIMARY}; spacing: 10px; font-size: 12px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {_R_BORDER_BRIGHT};
    background-color: {_R_BG_CARD}; border-radius: 2px;
}}
QCheckBox::indicator:checked  {{ background-color: {SUCCESS}; border-color: {SUCCESS}; }}
QCheckBox::indicator:hover    {{ border-color: {_R_ACCENT}; }}
QCheckBox:disabled            {{ color: {_R_TEXT_MUTED}; }}
QComboBox {{
    background-color: {_R_BG_CARD}; color: {_R_TEXT_PRIMARY};
    border: 1px solid {_R_BORDER_BRIGHT}; border-radius: 2px;
    padding: 3px 8px; font-family: {FONT}; font-size: 11px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{
    border-left: 5px solid transparent; border-right: 5px solid transparent;
    border-top: 6px solid {_R_ACCENT}; width: 0; height: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {_R_BG_CARD}; color: {_R_TEXT_PRIMARY};
    border: 1px solid {_R_BORDER_BRIGHT};
    selection-background-color: {_R_ACCENT_BLUE}; font-family: {FONT};
}}
QLineEdit, QSpinBox, QDateEdit {{
    background-color: {_R_BG_CARD}; color: {_R_TEXT_PRIMARY};
    border: 1px solid {_R_BORDER_BRIGHT}; border-radius: 2px;
    padding: 4px 8px; font-family: {FONT}; font-size: 12px;
}}
QLineEdit:focus, QSpinBox:focus {{ border-color: {_R_ACCENT}; }}
QSlider::groove:horizontal {{
    background: {_R_BG_CARD}; border: 1px solid {_R_BORDER_DIM};
    height: 4px; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{ background: {_R_ACCENT_BLUE}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {_R_ACCENT}; border: 1px solid {_R_ACCENT};
    width: 12px; height: 12px; margin: -4px 0; border-radius: 6px;
}}
QGroupBox {{
    color: {_R_ACCENT}; border: 1px solid {_R_BORDER_BRIGHT};
    border-radius: 3px; margin-top: 12px; padding: 10px 8px 8px 8px;
    font-size: 10px; font-weight: bold; letter-spacing: 2px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
QScrollBar:vertical {{ background: {_R_BG_DARK}; width: 6px; border: none; }}
QScrollBar::handle:vertical {{ background: {_R_BORDER_BRIGHT}; border-radius: 3px; min-height: 20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {_R_BG_DARK}; height: 6px; border: none; }}
QScrollBar::handle:horizontal {{ background: {_R_BORDER_BRIGHT}; border-radius: 3px; min-width: 20px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QToolTip {{
    background-color: {_R_BG_PANEL}; color: {_R_TEXT_PRIMARY};
    border: 1px solid {_R_ACCENT}; font-family: {FONT}; font-size: 11px; padding: 4px;
}}
"""


def get_stylesheet(theme: str = "cyan") -> str:
    return STYLESHEET_RED if theme == "red" else STYLESHEET
