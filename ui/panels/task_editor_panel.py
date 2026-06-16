"""Task editor panel — manage custom tasks and set skill proficiency goals."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
    STYLESHEET,
)

_CATEGORIES  = ["PROJECT", "THEORY", "SKILL", "CUSTOM"]
_SKILL_RANKS = ["", "E", "D", "C", "B", "A", "S"]


class _TaskRow(QWidget):
    """One row for an active task with edit/remove controls."""

    remove_requested = Signal(int)
    edit_requested   = Signal(int, str, str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self._task_id = task["task_id"]
        self.setMinimumHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        # Category tag
        cat_colors = {"PROJECT": "#ff7700", "THEORY": "#00aaff",
                      "SKILL": "#bb44ff", "CUSTOM": ACCENT_CYAN}
        cat = QLabel(f"[{task['category']}]")
        cat.setFixedWidth(72)
        cat.setStyleSheet(
            f"color: {cat_colors.get(task['category'], ACCENT_CYAN)}; "
            f"font-size: 9px; font-weight: bold; background: transparent;"
        )
        lay.addWidget(cat)

        # Name
        name = QLabel(task["name"])
        name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; background: transparent;")
        lay.addWidget(name)
        lay.addStretch()

        # Rewards
        rwd = QLabel(f"+{task['exp_reward']} EXP  +{task['gold_reward']} G")
        rwd.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;")
        lay.addWidget(rwd)

        # Edit button
        edit_btn = QPushButton("EDIT")
        edit_btn.setFixedWidth(50)
        edit_btn.setStyleSheet(
            f"color: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; font-size: 9px; padding: 2px 6px;"
        )
        edit_btn.clicked.connect(self._on_edit)
        lay.addWidget(edit_btn)

        # Remove button (only for non-default tasks or any task)
        rm_btn = QPushButton("✕")
        rm_btn.setFixedWidth(30)
        rm_btn.setObjectName("dangerBtn")
        rm_btn.setStyleSheet(
            f"color: {DANGER}; border-color: {DANGER}; font-size: 11px; padding: 2px 4px;"
        )
        rm_btn.clicked.connect(lambda: self.remove_requested.emit(self._task_id))
        lay.addWidget(rm_btn)

        self._task = task

    def _on_edit(self) -> None:
        dlg = _EditTaskDialog(self._task, self.window())
        if dlg.exec() == QDialog.Accepted:
            self.edit_requested.emit(self._task_id, dlg.name(), dlg.category())

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class _EditTaskDialog(QDialog):
    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")
        self.setStyleSheet(STYLESHEET)
        self.setMinimumWidth(360)

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        lay.addWidget(QLabel("Task name:"))
        self._name = QLineEdit(task["name"])
        lay.addWidget(self._name)

        lay.addWidget(QLabel("Category:"))
        self._cat = QComboBox()
        self._cat.addItems(_CATEGORIES)
        if task["category"] in _CATEGORIES:
            self._cat.setCurrentIndex(_CATEGORIES.index(task["category"]))
        lay.addWidget(self._cat)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def name(self) -> str:
        return self._name.text().strip()

    def category(self) -> str:
        return self._cat.currentText()


class _GoalRow(QWidget):
    """One row for a skill goal with rank/deadline selector."""

    goal_changed = Signal(str, str, str)

    def __init__(self, skill: dict, goal: dict, parent=None):
        super().__init__(parent)
        self._skill_name = skill["skill_name"]
        self.setMinimumHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        # Skill name
        name = QLabel(self._skill_name)
        name.setFixedWidth(90)
        name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; background: transparent;")
        lay.addWidget(name)

        # Current rank
        cur_rank = skill.get("current_rank", "F")
        _RANK_COLOR = {"F": TEXT_MUTED, "E": TEXT_SECONDARY, "D": ACCENT_CYAN,
                       "C": SUCCESS, "B": WARNING, "A": "#ff6600", "S": GOLD}
        cur = QLabel(f"Current: {cur_rank}")
        cur.setFixedWidth(80)
        cur.setStyleSheet(
            f"color: {_RANK_COLOR.get(cur_rank, TEXT_MUTED)}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(cur)

        # Target rank selector
        lbl_target = QLabel("Target:")
        lbl_target.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        lay.addWidget(lbl_target)

        self._rank_combo = QComboBox()
        self._rank_combo.addItems(["(none)", "E", "D", "C", "B", "A", "S"])
        target = goal.get("target_rank", "")
        if target in _SKILL_RANKS[1:]:
            self._rank_combo.setCurrentIndex(_SKILL_RANKS[1:].index(target) + 1)
        self._rank_combo.setFixedWidth(70)
        self._rank_combo.currentTextChanged.connect(self._on_changed)
        lay.addWidget(self._rank_combo)

        # Deadline (optional text)
        lbl_dl = QLabel("By:")
        lbl_dl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        lay.addWidget(lbl_dl)

        self._deadline = QLineEdit(goal.get("deadline", ""))
        self._deadline.setPlaceholderText("YYYY-MM-DD")
        self._deadline.setFixedWidth(100)
        self._deadline.editingFinished.connect(self._on_changed)
        lay.addWidget(self._deadline)

        lay.addStretch()

        # Progress indicator
        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;")
        lay.addWidget(self._progress_lbl)
        self._update_progress(skill, goal)

    def _update_progress(self, skill: dict, goal: dict) -> None:
        target = goal.get("target_rank", "")
        if not target:
            self._progress_lbl.setText("")
            return
        _RANK_ORDER = {"F": 0, "E": 1, "D": 2, "C": 3, "B": 4, "A": 5, "S": 6}
        cur_v  = _RANK_ORDER.get(skill.get("current_rank", "F"), 0)
        tgt_v  = _RANK_ORDER.get(target, 0)
        if cur_v >= tgt_v:
            self._progress_lbl.setText("✔ ACHIEVED")
            self._progress_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 9px; background: transparent;")
        else:
            self._progress_lbl.setText(f"{cur_v}/{tgt_v} ranks")
            self._progress_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;")

    def _on_changed(self) -> None:
        rank = self._rank_combo.currentText()
        if rank == "(none)":
            rank = ""
        deadline = self._deadline.text().strip()
        self.goal_changed.emit(self._skill_name, rank, deadline)

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class TaskEditorPanel(QWidget):
    """Panel for managing tasks and skill goals."""

    tasks_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_rows: dict[int, _TaskRow] = {}
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        hdr = QLabel("[!]  TASK  MANAGER  &  SKILL  GOALS")
        hdr.setObjectName("questTitle")
        outer.addWidget(hdr)

        # ── Tasks section ──
        task_grp = QGroupBox("TASK MANAGEMENT")
        task_lay = QVBoxLayout(task_grp)
        task_lay.setSpacing(4)

        # Add task form
        add_row = QHBoxLayout()
        self._new_name = QLineEdit()
        self._new_name.setPlaceholderText("New task name…")
        self._new_name.returnPressed.connect(self._on_add_task)
        add_row.addWidget(self._new_name)

        self._new_cat = QComboBox()
        self._new_cat.addItems(_CATEGORIES)
        self._new_cat.setFixedWidth(90)
        add_row.addWidget(self._new_cat)

        add_btn = QPushButton("ADD")
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._on_add_task)
        add_row.addWidget(add_btn)
        task_lay.addLayout(add_row)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 10px;")
        task_lay.addWidget(self._status_lbl)

        # Task scroll area
        scroll_t = QScrollArea()
        scroll_t.setWidgetResizable(True)
        scroll_t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_t.setFixedHeight(200)
        from PySide6.QtWidgets import QFrame
        scroll_t.setFrameShape(QFrame.NoFrame)

        self._tasks_content = QWidget()
        self._tasks_content.setStyleSheet("background: transparent;")
        self._tasks_layout = QVBoxLayout(self._tasks_content)
        self._tasks_layout.setContentsMargins(0, 0, 0, 0)
        self._tasks_layout.setSpacing(2)
        self._tasks_layout.addStretch()
        scroll_t.setWidget(self._tasks_content)
        task_lay.addWidget(scroll_t)
        outer.addWidget(task_grp)

        # ── Skill Goals section ──
        goal_grp = QGroupBox("SKILL PROFICIENCY GOALS")
        goal_lay = QVBoxLayout(goal_grp)
        goal_lay.setContentsMargins(8, 8, 8, 8)
        goal_lay.setSpacing(2)

        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        scroll_g.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_g.setFixedHeight(260)
        scroll_g.setFrameShape(QFrame.NoFrame)

        self._goals_content = QWidget()
        self._goals_content.setStyleSheet("background: transparent;")
        self._goals_layout = QVBoxLayout(self._goals_content)
        self._goals_layout.setContentsMargins(0, 0, 0, 0)
        self._goals_layout.setSpacing(2)
        self._goals_layout.addStretch()
        scroll_g.setWidget(self._goals_content)
        goal_lay.addWidget(scroll_g)
        outer.addWidget(goal_grp)

        # ── Study Resources section ──
        res_grp = QGroupBox("STUDY RESOURCES")
        res_lay = QVBoxLayout(res_grp)
        res_lay.setContentsMargins(8, 8, 8, 8)
        res_lay.setSpacing(6)

        # Add-resource form
        add_res_row = QHBoxLayout()
        self._res_skill = QComboBox()
        from database import SKILLS
        self._res_skill.addItems(SKILLS)
        self._res_skill.setFixedWidth(110)
        add_res_row.addWidget(self._res_skill)

        self._res_title = QLineEdit()
        self._res_title.setPlaceholderText("Resource title…")
        add_res_row.addWidget(self._res_title)

        self._res_url = QLineEdit()
        self._res_url.setPlaceholderText("URL (optional)")
        self._res_url.setFixedWidth(180)
        add_res_row.addWidget(self._res_url)

        add_res_btn = QPushButton("ADD")
        add_res_btn.setFixedWidth(52)
        add_res_btn.clicked.connect(self._on_add_resource)
        add_res_row.addWidget(add_res_btn)
        res_lay.addLayout(add_res_row)

        scroll_r = QScrollArea()
        scroll_r.setWidgetResizable(True)
        scroll_r.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_r.setFixedHeight(180)
        scroll_r.setFrameShape(QFrame.NoFrame)

        self._res_content = QWidget()
        self._res_content.setStyleSheet("background: transparent;")
        self._res_layout = QVBoxLayout(self._res_content)
        self._res_layout.setContentsMargins(0, 0, 0, 0)
        self._res_layout.setSpacing(2)
        self._res_layout.addStretch()
        scroll_r.setWidget(self._res_content)
        res_lay.addWidget(scroll_r)
        outer.addWidget(res_grp)

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_add_task(self) -> None:
        name = self._new_name.text().strip()
        if not name:
            return
        cat = self._new_cat.currentText()
        db.add_task(name, cat)
        self._new_name.clear()
        self._status_lbl.setText(f"[ Added: {name} ]")
        self.tasks_changed.emit()
        self.refresh()

    def _on_remove_task(self, task_id: int) -> None:
        if QMessageBox.question(
            self, "Remove Task",
            "Remove this task? (Completion history is kept)",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            db.remove_task(task_id)
            self.tasks_changed.emit()
            self.refresh()

    def _on_edit_task(self, task_id: int, name: str, cat: str) -> None:
        if name:
            db.update_task(task_id, name=name, category=cat)
            self.tasks_changed.emit()
            self.refresh()

    def _on_goal_changed(self, skill_name: str, target_rank: str, deadline: str) -> None:
        if target_rank:
            db.set_skill_goal(skill_name, target_rank, deadline)
        else:
            db.clear_skill_goal(skill_name)

    def _on_add_resource(self) -> None:
        title = self._res_title.text().strip()
        if not title:
            return
        skill = self._res_skill.currentText()
        url   = self._res_url.text().strip()
        db.add_resource(skill, title, url)
        self._res_title.clear()
        self._res_url.clear()
        self._refresh_resources()

    def _on_remove_resource(self, resource_id: int) -> None:
        db.remove_resource(resource_id)
        self._refresh_resources()

    def _refresh_resources(self) -> None:
        while self._res_layout.count() > 1:
            item = self._res_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        resources = db.get_resources()
        for res in resources:
            row = QWidget()
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(6, 3, 6, 3)
            r_lay.setSpacing(8)

            skill_lbl = QLabel(f"[{res['skill_name']}]")
            skill_lbl.setFixedWidth(90)
            skill_lbl.setStyleSheet(
                f"color: {ACCENT_CYAN}; font-size: 9px; font-weight: bold; background: transparent;"
            )
            r_lay.addWidget(skill_lbl)

            title_lbl = QLabel(res["title"])
            title_lbl.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 10px; background: transparent;"
            )
            r_lay.addWidget(title_lbl)
            r_lay.addStretch()

            if res.get("url"):
                url_lbl = QLabel(res["url"][:40] + ("…" if len(res["url"]) > 40 else ""))
                url_lbl.setStyleSheet(
                    f"color: {TEXT_MUTED}; font-size: 9px; background: transparent;"
                )
                r_lay.addWidget(url_lbl)

            rm = QPushButton("✕")
            rm.setFixedWidth(26)
            rm.setObjectName("dangerBtn")
            rm.setStyleSheet(
                f"color: {DANGER}; border-color: {DANGER}; font-size: 10px; padding: 1px 3px;"
            )
            rm.clicked.connect(lambda _, rid=res["id"]: self._on_remove_resource(rid))
            r_lay.addWidget(rm)

            self._res_layout.insertWidget(self._res_layout.count() - 1, row)

    # ── Public ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        # Rebuild task rows
        while self._tasks_layout.count() > 1:
            item = self._tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = db.get_tasks()
        for task in tasks:
            row = _TaskRow(task)
            row.remove_requested.connect(self._on_remove_task)
            row.edit_requested.connect(self._on_edit_task)
            self._tasks_layout.insertWidget(self._tasks_layout.count() - 1, row)

        # Rebuild goal rows
        while self._goals_layout.count() > 1:
            item = self._goals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        skills = db.get_all_skills()
        goals  = db.get_skill_goals()
        for skill in skills:
            goal = goals.get(skill["skill_name"], {})
            row  = _GoalRow(skill, goal)
            row.goal_changed.connect(self._on_goal_changed)
            self._goals_layout.insertWidget(self._goals_layout.count() - 1, row)

        self._refresh_resources()
