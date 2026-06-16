"""Gold Shop panel — spend gold on consumable boosts and items."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

import database as db
from ui.theme import (
    ACCENT_CYAN, BG_CARD, BG_PANEL, BORDER_BRIGHT, BORDER_DIM,
    DANGER, GOLD, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING,
)


class _ShopItemCard(QWidget):
    """Single shop item with buy/use buttons."""

    buy_requested = Signal(str)
    use_requested = Signal(str)

    def __init__(self, item: dict, quantity: int, parent=None):
        super().__init__(parent)
        self._item_id = item["item_id"]
        self.setMinimumHeight(90)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        # Icon
        icon_lbl = QLabel(item["icon"])
        icon_lbl.setFixedWidth(32)
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {GOLD}; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon_lbl)

        # Name + description
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(item["name"])
        name_lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 12px; font-weight: bold; letter-spacing: 1px; background: transparent;"
        )
        desc_lbl = QLabel(item["desc"])
        desc_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        info.addWidget(name_lbl)
        info.addWidget(desc_lbl)
        lay.addLayout(info)
        lay.addStretch()

        # Cost + qty + buttons
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setAlignment(Qt.AlignCenter)

        cost_lbl = QLabel(f"{item['cost']} GOLD")
        cost_lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 11px; font-weight: bold; background: transparent;"
        )
        cost_lbl.setAlignment(Qt.AlignRight)
        right.addWidget(cost_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._buy_btn = QPushButton("BUY")
        self._buy_btn.setFixedWidth(60)
        self._buy_btn.clicked.connect(lambda: self.buy_requested.emit(self._item_id))
        btn_row.addWidget(self._buy_btn)

        self._qty_lbl = QLabel(f"x{quantity}")
        self._qty_lbl.setFixedWidth(28)
        self._qty_lbl.setAlignment(Qt.AlignCenter)
        self._qty_lbl.setStyleSheet(
            f"color: {ACCENT_CYAN}; font-size: 11px; font-weight: bold; background: transparent;"
        )
        btn_row.addWidget(self._qty_lbl)

        self._use_btn = QPushButton("USE")
        self._use_btn.setFixedWidth(60)
        self._use_btn.setEnabled(quantity > 0)
        self._use_btn.clicked.connect(lambda: self.use_requested.emit(self._item_id))
        btn_row.addWidget(self._use_btn)

        right.addLayout(btn_row)
        lay.addLayout(right)

    def update_quantity(self, qty: int) -> None:
        self._qty_lbl.setText(f"x{qty}")
        self._use_btn.setEnabled(qty > 0)

    def paintEvent(self, _) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG_CARD))
        p.setPen(QPen(QColor(BORDER_DIM), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(0, 0, w - 1, h - 1)
        p.end()


class ShopPanel(QWidget):
    """Gold shop — buy and use consumable items."""

    purchase_made = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._item_cards: dict[str, _ShopItemCard] = {}
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Header row
        hdr_row = QHBoxLayout()
        hdr = QLabel("[!]  HUNTER'S  SHOP  —  SPEND  GOLD  WISELY")
        hdr.setObjectName("questTitle")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self._gold_lbl = QLabel("GOLD: 0")
        self._gold_lbl.setObjectName("goldLabel")
        hdr_row.addWidget(self._gold_lbl)
        outer.addLayout(hdr_row)

        # Active boosts display
        self._boost_lbl = QLabel("Active boosts: none")
        self._boost_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px;")
        outer.addWidget(self._boost_lbl)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER_DIM};")
        outer.addWidget(sep)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from PySide6.QtWidgets import QFrame
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        items_lay = QVBoxLayout(content)
        items_lay.setContentsMargins(0, 4, 0, 4)
        items_lay.setSpacing(6)

        for item in db.SHOP_ITEMS:
            card = _ShopItemCard(item, 0)
            card.buy_requested.connect(self._on_buy)
            card.use_requested.connect(self._on_use)
            items_lay.addWidget(card)
            self._item_cards[item["item_id"]] = card

        items_lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Status label
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; padding: 4px;")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._status_lbl)

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_buy(self, item_id: str) -> None:
        result = db.purchase_item(item_id)
        if result["success"]:
            self._status_lbl.setText(f"[ {result['message']} ]")
            self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; padding: 4px;")
            self.purchase_made.emit()
        else:
            self._status_lbl.setText(f"[ {result['message']} ]")
            self._status_lbl.setStyleSheet(f"color: {DANGER}; font-size: 11px; padding: 4px;")
        self.refresh()

    def _on_use(self, item_id: str) -> None:
        result = db.use_item(item_id)
        if result["success"]:
            self._status_lbl.setText("[ Item used! ]")
            self._status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; padding: 4px;")
            self.purchase_made.emit()
        else:
            self._status_lbl.setText(f"[ {result.get('message', 'Error')} ]")
            self._status_lbl.setStyleSheet(f"color: {DANGER}; font-size: 11px; padding: 4px;")
        self.refresh()

    # ── Public ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        hunter    = db.get_hunter()
        inventory = db.get_shop_inventory()
        boosts    = db.get_active_boosts()

        self._gold_lbl.setText(f"GOLD: {hunter.get('gold', 0):,}")

        for item_id, card in self._item_cards.items():
            card.update_quantity(inventory.get(item_id, 0))

        if boosts:
            names = {"exp_boost": "EXP x2", "gold_boost": "GOLD x2"}
            active_str = " | ".join(names.get(k, k) for k in boosts)
            self._boost_lbl.setText(f"Active boosts: {active_str}")
            self._boost_lbl.setStyleSheet(f"color: {WARNING}; font-size: 11px;")
        else:
            self._boost_lbl.setText("Active boosts: none")
            self._boost_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
