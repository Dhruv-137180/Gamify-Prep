"""Settings panel — backup/restore, reminder config, particles, prestige."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)


class SettingsPanel(QWidget):
    """Central settings hub."""

    particles_toggled  = Signal(bool)
    prestige_performed = Signal(dict)     # emits do_prestige() result

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        hdr = QLabel("[⚙]  SETTINGS  &  SYSTEM  CONFIG")
        hdr.setObjectName("questTitle")
        outer.addWidget(hdr)

        outer.addWidget(self._mk_backup_group())
        outer.addWidget(self._mk_prestige_group())
        outer.addWidget(self._mk_reminder_group())
        outer.addWidget(self._mk_display_group())
        outer.addStretch()

    # ── Backup / Restore ──────────────────────────────────────────────────────

    def _mk_backup_group(self) -> QGroupBox:
        grp = QGroupBox("DATABASE BACKUP & RESTORE")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        info = QLabel(
            "Backup exports your entire hunter database (progress, skills, history).\n"
            "Restore replaces the current database with a previously saved file."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        lay.addWidget(info)

        btn_row = QHBoxLayout()

        backup_btn = QPushButton("BACKUP DATABASE")
        backup_btn.setFixedWidth(160)
        backup_btn.clicked.connect(self._on_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("RESTORE DATABASE")
        restore_btn.setFixedWidth(160)
        restore_btn.setObjectName("warnBtn")
        restore_btn.clicked.connect(self._on_restore)
        btn_row.addWidget(restore_btn)

        btn_row.addStretch()
        lay.addLayout(btn_row)

        export_row = QHBoxLayout()
        json_btn = QPushButton("EXPORT  JSON  REPORT")
        json_btn.setFixedWidth(160)
        json_btn.clicked.connect(self._on_export_json)
        export_row.addWidget(json_btn)

        html_btn = QPushButton("EXPORT  HTML  REPORT")
        html_btn.setFixedWidth(160)
        html_btn.clicked.connect(self._on_export_html)
        export_row.addWidget(html_btn)
        export_row.addStretch()
        lay.addLayout(export_row)

        self._backup_status = QLabel("")
        self._backup_status.setStyleSheet(f"color: {SUCCESS}; font-size: 10px;")
        lay.addWidget(self._backup_status)

        return grp

    # ── Prestige ──────────────────────────────────────────────────────────────

    def _mk_prestige_group(self) -> QGroupBox:
        grp = QGroupBox("PRESTIGE SYSTEM")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        self._prestige_info = QLabel("")
        self._prestige_info.setWordWrap(True)
        self._prestige_info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        lay.addWidget(self._prestige_info)

        btn_row = QHBoxLayout()
        self._prestige_btn = QPushButton("PERFORM PRESTIGE RESET")
        self._prestige_btn.setObjectName("dangerBtn")
        self._prestige_btn.setFixedWidth(200)
        self._prestige_btn.clicked.connect(self._on_prestige)
        btn_row.addWidget(self._prestige_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._prestige_log_lbl = QLabel("")
        self._prestige_log_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        lay.addWidget(self._prestige_log_lbl)

        return grp

    # ── Reminder ──────────────────────────────────────────────────────────────

    def _mk_reminder_group(self) -> QGroupBox:
        grp = QGroupBox("DAILY QUEST REMINDER")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        row1 = QHBoxLayout()
        self._reminder_chk = QCheckBox("Enable daily reminder notification")
        self._reminder_chk.toggled.connect(self._on_reminder_toggle)
        row1.addWidget(self._reminder_chk)
        row1.addStretch()
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Reminder hour (24h):"))
        self._reminder_hour = QSpinBox()
        self._reminder_hour.setRange(0, 23)
        self._reminder_hour.setFixedWidth(70)
        self._reminder_hour.valueChanged.connect(self._on_reminder_hour)
        row2.addWidget(self._reminder_hour)
        row2.addWidget(QLabel("(checks within ±5 minutes of this hour)"))
        row2.addStretch()
        lay.addLayout(row2)

        return grp

    # ── Display ───────────────────────────────────────────────────────────────

    def _mk_display_group(self) -> QGroupBox:
        grp = QGroupBox("DISPLAY")
        lay = QVBoxLayout(grp)
        lay.setSpacing(8)

        row = QHBoxLayout()
        self._particle_chk = QCheckBox("Enable animated particle background")
        self._particle_chk.toggled.connect(self._on_particle_toggle)
        row.addWidget(self._particle_chk)
        row.addStretch()
        lay.addLayout(row)

        note = QLabel("Particles are decorative only and have no gameplay effect.")
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px;")
        lay.addWidget(note)

        return grp

    # ── Slot handlers ─────────────────────────────────────────────────────────

    def _on_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", "hunter_backup.db", "Database Files (*.db)"
        )
        if not path:
            return
        try:
            db.backup_db(path)
            self._backup_status.setText(f"[ Backup saved: {path} ]")
            self._backup_status.setStyleSheet(f"color: {SUCCESS}; font-size: 10px;")
        except Exception as e:
            self._backup_status.setText(f"[ ERROR: {e} ]")
            self._backup_status.setStyleSheet(f"color: {DANGER}; font-size: 10px;")

    def _on_restore(self):
        if QMessageBox.warning(
            self, "Restore Database",
            "This will REPLACE your current database with the backup file.\n"
            "All current progress will be lost. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Backup", "", "Database Files (*.db)"
        )
        if not path:
            return
        try:
            db.restore_db(path)
            self._backup_status.setText("[ Restore complete — please restart the app ]")
            self._backup_status.setStyleSheet(f"color: {WARNING}; font-size: 10px;")
        except Exception as e:
            self._backup_status.setText(f"[ ERROR: {e} ]")
            self._backup_status.setStyleSheet(f"color: {DANGER}; font-size: 10px;")

    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON Report", "hunter_report.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            db.export_progress_json(path)
            self._backup_status.setText(f"[ JSON exported: {path} ]")
            self._backup_status.setStyleSheet(f"color: {SUCCESS}; font-size: 10px;")
        except Exception as e:
            self._backup_status.setText(f"[ ERROR: {e} ]")
            self._backup_status.setStyleSheet(f"color: {DANGER}; font-size: 10px;")

    def _on_export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export HTML Report", "hunter_report.html", "HTML Files (*.html)"
        )
        if not path:
            return
        try:
            db.export_progress_html(path)
            self._backup_status.setText(f"[ HTML exported: {path} ]")
            self._backup_status.setStyleSheet(f"color: {SUCCESS}; font-size: 10px;")
        except Exception as e:
            self._backup_status.setText(f"[ ERROR: {e} ]")
            self._backup_status.setStyleSheet(f"color: {DANGER}; font-size: 10px;")

    def _on_prestige(self):
        if not db.can_prestige():
            QMessageBox.information(self, "PRESTIGE", "You must reach Level 60 (S-Rank) to prestige.")
            return
        hunter = db.get_hunter()
        confirm = QMessageBox.question(
            self, "CONFIRM PRESTIGE",
            f"You are about to prestige!\n\n"
            f"• Level will reset to 1\n"
            f"• EXP will reset to 0\n"
            f"• You keep {hunter['gold'] // 2:,} Gold (half of {hunter['gold']:,})\n"
            f"• You gain a special Prestige title\n\n"
            f"This cannot be undone. Proceed?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        result = db.do_prestige()
        if result.get("success"):
            self.prestige_performed.emit(result)
            self.refresh()

    def _on_reminder_toggle(self, checked: bool):
        db.set_setting("reminder_enabled", "1" if checked else "0")

    def _on_reminder_hour(self, value: int):
        db.set_setting("reminder_hour", str(value))

    def _on_particle_toggle(self, checked: bool):
        db.set_setting("particles_enabled", "1" if checked else "0")
        self.particles_toggled.emit(checked)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        hunter   = db.get_hunter()
        level    = hunter.get("level", 1)
        prestige = hunter.get("prestige_count", 0)

        if db.can_prestige():
            self._prestige_info.setText(
                f"You have reached Level {level} — PRESTIGE IS AVAILABLE!\n"
                f"Resetting will grant you the next prestige title and keep half your Gold."
            )
            self._prestige_btn.setEnabled(True)
        else:
            needed = max(0, 60 - level)
            self._prestige_info.setText(
                f"Prestige requires Level 60 (S-Rank).  "
                f"You are Level {level} — {needed} more level(s) needed."
            )
            self._prestige_btn.setEnabled(False)

        log = db.get_prestige_log()
        if log:
            lines = [f"Prestige {r['prestige_num']}: {r['prestige_date']}  (Lv {r['level_reached']})" for r in log]
            self._prestige_log_lbl.setText("  |  ".join(lines))
        else:
            self._prestige_log_lbl.setText("No prestige history yet.")

        # Reminder
        enabled = db.get_setting("reminder_enabled", "1") == "1"
        self._reminder_chk.blockSignals(True)
        self._reminder_chk.setChecked(enabled)
        self._reminder_chk.blockSignals(False)

        try:
            hour = int(db.get_setting("reminder_hour", "20"))
        except ValueError:
            hour = 20
        self._reminder_hour.blockSignals(True)
        self._reminder_hour.setValue(hour)
        self._reminder_hour.blockSignals(False)

        # Particles
        particles = db.get_setting("particles_enabled", "1") == "1"
        self._particle_chk.blockSignals(True)
        self._particle_chk.setChecked(particles)
        self._particle_chk.blockSignals(False)
