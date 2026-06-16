"""Skill tree — QPainter visualization of DV skills and their connections."""
from __future__ import annotations
import math

from PySide6.QtCore import Qt, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_DARK, BG_PANEL, BORDER_BRIGHT, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)

# Node definitions with fixed canvas positions (0-1 normalised)
_NODES = {
    "Python":      {"x": 0.10, "y": 0.45, "col": ACCENT_CYAN},
    "OOPS":        {"x": 0.10, "y": 0.20, "col": "#bb44ff"},
    "CDC":         {"x": 0.10, "y": 0.70, "col": WARNING},
    "Constraints": {"x": 0.38, "y": 0.30, "col": "#ff7700"},
    "Assertions":  {"x": 0.38, "y": 0.60, "col": "#00aaff"},
    "Covergroups": {"x": 0.38, "y": 0.80, "col": SUCCESS},
    "UVM":         {"x": 0.65, "y": 0.35, "col": GOLD},
    "Formal":      {"x": 0.65, "y": 0.70, "col": DANGER},
    "Testplan":    {"x": 0.88, "y": 0.50, "col": "#ff44aa"},
}

_EDGES = [
    ("OOPS",        "UVM"),
    ("Python",      "UVM"),
    ("Constraints", "UVM"),
    ("Constraints", "Formal"),
    ("Assertions",  "Formal"),
    ("Assertions",  "UVM"),
    ("Covergroups", "UVM"),
    ("UVM",         "Testplan"),
    ("Formal",      "Testplan"),
    ("CDC",         "Formal"),
]

_RANK_ORDER = {"F": 0, "E": 1, "D": 2, "C": 3, "B": 4, "A": 5, "S": 6}


class _SkillCanvas(QWidget):
    """QPainter skill-tree canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skills: dict[str, dict] = {}
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(320)

    def update_skills(self, skills: list[dict]):
        self._skills = {s["skill_name"]: s for s in skills}
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG_DARK))

        NODE_R = 32   # node circle radius

        def canvas_pos(nx: float, ny: float):
            return int(nx * w), int(ny * h)

        # Draw edges
        for src, dst in _EDGES:
            if src not in _NODES or dst not in _NODES:
                continue
            sx, sy = canvas_pos(_NODES[src]["x"], _NODES[src]["y"])
            dx, dy = canvas_pos(_NODES[dst]["x"], _NODES[dst]["y"])
            src_skill = self._skills.get(src, {})
            dst_skill = self._skills.get(dst, {})
            src_rank  = _RANK_ORDER.get(src_skill.get("current_rank", "F"), 0)
            dst_rank  = _RANK_ORDER.get(dst_skill.get("current_rank", "F"), 0)

            if src_rank >= 1 and dst_rank >= 1:
                edge_color = QColor(BORDER_BRIGHT)
                width = 2
            elif src_rank >= 1:
                edge_color = QColor(BORDER_DIM)
                edge_color.setAlpha(160)
                width = 1
            else:
                edge_color = QColor(BORDER_DIM)
                edge_color.setAlpha(70)
                width = 1

            pen = QPen(edge_color, width, Qt.SolidLine)
            p.setPen(pen)

            # Draw shortened line (from node edge to node edge)
            angle = math.atan2(dy - sy, dx - sx)
            p.drawLine(
                int(sx + NODE_R * math.cos(angle)),
                int(sy + NODE_R * math.sin(angle)),
                int(dx - NODE_R * math.cos(angle)),
                int(dy - NODE_R * math.sin(angle)),
            )

            # Arrow head
            if src_rank >= 1:
                ax = dx - NODE_R * math.cos(angle)
                ay = dy - NODE_R * math.sin(angle)
                arr = 8
                p.drawLine(
                    int(ax), int(ay),
                    int(ax - arr * math.cos(angle - 0.4)),
                    int(ay - arr * math.sin(angle - 0.4)),
                )
                p.drawLine(
                    int(ax), int(ay),
                    int(ax - arr * math.cos(angle + 0.4)),
                    int(ay - arr * math.sin(angle + 0.4)),
                )

        # Draw nodes
        for name, node_def in _NODES.items():
            cx, cy   = canvas_pos(node_def["x"], node_def["y"])
            skill    = self._skills.get(name, {})
            rank     = skill.get("current_rank", "F")
            rank_v   = _RANK_ORDER.get(rank, 0)
            pts      = skill.get("proficiency_points", 0)
            col_hex  = node_def["col"]
            base_col = QColor(col_hex)

            # Background fill
            bg = QColor(BG_CARD)
            if rank_v >= 4:
                bg = QColor(col_hex)
                bg.setAlpha(40)
            p.setBrush(bg)

            # Border
            border_col = QColor(col_hex) if rank_v >= 1 else QColor(BORDER_DIM)
            border_width = 2 if rank_v >= 2 else 1
            p.setPen(QPen(border_col, border_width))
            p.drawEllipse(cx - NODE_R, cy - NODE_R, NODE_R * 2, NODE_R * 2)

            # Skill name
            font = QFont("Consolas", 8, QFont.Bold)
            p.setFont(font)
            p.setPen(base_col if rank_v >= 1 else QColor(TEXT_SECONDARY))
            p.drawText(
                QRect(cx - NODE_R, cy - 8, NODE_R * 2, 16),
                Qt.AlignCenter,
                name,
            )

            # Rank label below
            rank_font = QFont("Consolas", 7)
            p.setFont(rank_font)
            rank_col = QColor(col_hex) if rank_v >= 1 else QColor(TEXT_MUTED)
            p.setPen(rank_col)
            p.drawText(
                QRect(cx - NODE_R, cy + 8, NODE_R * 2, 12),
                Qt.AlignCenter,
                f"[{rank}]  {pts}pts",
            )

            # Gold halo for S-rank
            if rank == "S":
                halo = QPen(QColor(GOLD), 3)
                halo.setStyle(Qt.DotLine)
                p.setPen(halo)
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(cx - NODE_R - 4, cy - NODE_R - 4, (NODE_R + 4) * 2, (NODE_R + 4) * 2)

        p.end()


class SkillTreePanel(QWidget):
    """Full skill-tree visualization panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        hdr = QLabel("[■]  SKILL  TREE  —  DV  ENGINEER  PATH")
        hdr.setObjectName("questTitle")
        lay.addWidget(hdr)

        self._canvas = _SkillCanvas()
        lay.addWidget(self._canvas, stretch=1)

        # Legend
        legend_row = QVBoxLayout()
        legend_row.setSpacing(2)

        legend_lbl = QLabel(
            "Node brightness = rank earned   ·   "
            "Edge brightness = connection unlocked   ·   "
            "Gold halo = S-Rank achieved"
        )
        legend_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px;")
        legend_row.addWidget(legend_lbl)

        rank_row_lbl = QLabel("Rank scale:  F → E → D → C → B → A → S")
        rank_row_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9px; letter-spacing: 1px;")
        legend_row.addWidget(rank_row_lbl)

        lay.addLayout(legend_row)

    def refresh(self):
        skills = db.get_all_skills()
        self._canvas.update_skills(skills)
