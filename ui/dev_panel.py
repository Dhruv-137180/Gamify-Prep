"""Dev Mode panel — time travel, DB reset, penalty testing."""
from datetime import date as _date, datetime, timezone, timedelta

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QDialog, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSpinBox, QDateEdit, QVBoxLayout,
)

import database as db
import date_helper
from ui.theme import STYLESHEET, WARNING, SUCCESS, TEXT_MUTED, DANGER


class DevPanel(QDialog):
    """Floating dev-tools window."""

    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("■ DEV MODE CONSOLE ■")
        self.setWindowFlag(Qt.Tool)
        self.setMinimumWidth(440)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        hdr = QLabel("⚠  DEV MODE — NOT FOR NORMAL PLAY  ⚠")
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(
            f"color: {WARNING}; font-weight: bold; font-size: 13px; padding: 6px;"
        )
        root.addWidget(hdr)

        root.addWidget(self._date_group())
        root.addWidget(self._profile_group())
        root.addWidget(self._penalty_group())
        root.addWidget(self._db_group())

        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; padding: 4px;")
        root.addWidget(self._status_lbl)

    # ── Groups ─────────────────────────────────────────────────────────

    def _date_group(self) -> QGroupBox:
        grp = QGroupBox("DATE / TIME CONTROL")
        lay = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("Simulated date:"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setFixedWidth(130)
        row.addWidget(self._date_edit)
        row.addStretch()
        lay.addLayout(row)

        btns = QHBoxLayout()
        for label, slot in [
            ("SET DATE",      self._on_set_date),
            ("REAL DATE",     self._on_clear_date),
            ("▶ +1 DAY",      self._on_advance),
        ]:
            b = QPushButton(label)
            if label == "▶ +1 DAY":
                b.setObjectName("warnBtn")
            b.clicked.connect(slot)
            btns.addWidget(b)
        lay.addLayout(btns)

        self._date_readout = QLabel()
        self._date_readout.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        lay.addWidget(self._date_readout)
        self._update_readout()
        return grp

    def _profile_group(self) -> QGroupBox:
        grp = QGroupBox("HUNTER PROFILE TWEAKS")
        lay = QVBoxLayout(grp)

        for label, attr, default in [
            ("Grant EXP:",  "_exp_spin",  150),
            ("Grant Gold:", "_gold_spin", 100),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            spin = QSpinBox()
            spin.setRange(0, 99_999)
            spin.setValue(default)
            spin.setFixedWidth(90)
            setattr(self, attr, spin)
            row.addWidget(spin)
            btn = QPushButton("GRANT")
            btn.clicked.connect(
                (self._on_grant_exp if "EXP" in label else self._on_grant_gold)
            )
            row.addWidget(btn)
            row.addStretch()
            lay.addLayout(row)

        rst = QPushButton("RESET PROFILE TO LEVEL 1")
        rst.setObjectName("warnBtn")
        rst.clicked.connect(self._on_reset_profile)
        lay.addWidget(rst)
        return grp

    def _penalty_group(self) -> QGroupBox:
        grp = QGroupBox("PENALTY ZONE")
        lay = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("Timer (seconds):"))
        self._timer_spin = QSpinBox()
        self._timer_spin.setRange(5, 2700)
        self._timer_spin.setValue(10)
        self._timer_spin.setFixedWidth(80)
        self._timer_spin.setToolTip("10 s is great for testing; real value = 2700 (45 min)")
        row.addWidget(self._timer_spin)
        row.addStretch()
        lay.addLayout(row)

        btns = QHBoxLayout()
        force = QPushButton("▶ FORCE PENALTY")
        force.setObjectName("dangerBtn")
        force.clicked.connect(self._on_force_penalty)
        clr = QPushButton("CLEAR PENALTY")
        clr.clicked.connect(self._on_clear_penalty)
        btns.addWidget(force)
        btns.addWidget(clr)
        lay.addLayout(btns)
        return grp

    def _db_group(self) -> QGroupBox:
        grp = QGroupBox("DATABASE")
        lay = QVBoxLayout(grp)
        btn = QPushButton("■ WIPE & RE-SEED DATABASE ■")
        btn.setObjectName("dangerBtn")
        btn.clicked.connect(self._on_reset_db)
        lay.addWidget(btn)
        return grp

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_set_date(self):
        qd = self._date_edit.date()
        date_helper.set_simulated_date(_date(qd.year(), qd.month(), qd.day()))
        self._update_readout()
        self._status(f"Date locked → {date_helper.get_today_str()}")
        self.refresh_requested.emit()

    def _on_clear_date(self):
        date_helper.clear_simulated_date()
        self._update_readout()
        self._status("Using real system date")
        self.refresh_requested.emit()

    def _on_advance(self):
        date_helper.advance_day()
        new = date_helper.get_today_str()
        self._date_edit.setDate(QDate.fromString(new, "yyyy-MM-dd"))
        self._update_readout()
        self._status(f"Advanced → {new}")
        self.refresh_requested.emit()

    def _on_grant_exp(self):
        amt = self._exp_spin.value()
        h = db.get_hunter()
        db.update_hunter(current_exp=h["current_exp"] + amt)
        self._status(f"+{amt} EXP  (level-up fires on refresh)")
        self.refresh_requested.emit()

    def _on_grant_gold(self):
        amt = self._gold_spin.value()
        h = db.get_hunter()
        db.update_hunter(gold=h["gold"] + amt)
        self._status(f"+{amt} Gold")
        self.refresh_requested.emit()

    def _on_reset_profile(self):
        db.update_hunter(
            level=1, current_exp=0, next_level_exp=100,
            gold=0, title="E-Rank Garbage", streak=0, best_streak=0,
        )
        self._status("Profile reset → Level 1")
        self.refresh_requested.emit()

    def _on_force_penalty(self):
        secs     = self._timer_spin.value()
        deadline = (datetime.now(timezone.utc) + timedelta(seconds=secs)).isoformat()
        db.set_setting("penalty_deadline", deadline)
        self._status(f"Penalty deadline set ({secs}s from now)")
        self.refresh_requested.emit()

    def _on_clear_penalty(self):
        db.set_setting("penalty_deadline", "")
        self._status("Penalty cleared")
        self.refresh_requested.emit()

    def _on_reset_db(self):
        if QMessageBox.question(
            self, "RESET DATABASE",
            "Erase ALL progress and re-seed from scratch?\n",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            db.reset_db()
            date_helper.clear_simulated_date()
            self._update_readout()
            self._status("Database wiped and re-seeded")
            self.refresh_requested.emit()

    # ── Helpers ────────────────────────────────────────────────────────

    def _update_readout(self):
        today = date_helper.get_today_str()
        tag   = " [SIM]" if date_helper.is_simulated() else " [REAL]"
        self._date_readout.setText(f"Active date: {today}{tag}")

    def _status(self, msg: str):
        self._status_lbl.setText(f"[ {msg} ]")
