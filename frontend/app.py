import sys

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import api_client

# ---- Palette: enterprise / finance-dashboard neutral, one confident accent ----
NAVY = "#14284B"
NAVY_SOFT = "#A9B7D1"
BG = "#F4F6F8"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F9FAFB"
LINE = "#E2E6EA"
INK = "#1A1F29"
INK_SOFT = "#6B7280"
ACCENT = "#2458B3"
ACCENT_DARK = "#1E4A96"
ACCENT_DISABLED = "#B7C6E3"
WARN = "#B7791F"
DANGER = "#C0392B"
DANGER_SOFT = "#FDEDEC"

# loan_type -> (tab label, amount range, rate range, tenure range) — each range is (min, max, default, step)
LOAN_TYPE_CONFIG = {
    "home": {
        "label": "Home Loan",
        "amount": (100_000, 20_000_000, 5_000_000, 50_000),
        "rate": (5, 15, 8.5, 0.05),
        "tenure": (1, 30, 20, 1),
    },
    "car": {
        "label": "Car Loan",
        "amount": (50_000, 3_000_000, 800_000, 25_000),
        "rate": (7, 16, 10.5, 0.05),
        "tenure": (1, 7, 5, 1),
    },
}
LOAN_TYPE_ORDER = ["home", "car"]

STYLESHEET = f"""
QMainWindow {{ background: {BG}; }}
QWidget {{ color: {INK}; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 13px; }}

QFrame#header {{ background: {NAVY}; }}
QLabel#headerTitle {{ color: #FFFFFF; font-size: 18px; font-weight: 700; }}
QLabel#headerSubtitle {{ color: {NAVY_SOFT}; font-size: 11.5px; }}
QLabel#headerRole {{ color: {NAVY_SOFT}; font-size: 10.5px; letter-spacing: 0.5px; }}
QToolButton#accountBtn {{
    background: transparent;
    color: #FFFFFF;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12.5px;
    font-weight: 600;
}}
QToolButton#accountBtn:hover {{ background: rgba(255,255,255,0.1); border-color: {NAVY_SOFT}; }}
QToolButton#accountBtn::menu-indicator {{ subcontrol-position: right center; subcontrol-origin: padding; right: 4px; }}
QMenu {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 5px;
    color: {INK};
    font-size: 12.5px;
}}
QMenu::item:selected {{ background: {ACCENT}; color: #FFFFFF; }}
QMenu::separator {{ height: 1px; background: {LINE}; margin: 4px 6px; }}

QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar {{ font-size: 12.5px; }}
QTabBar::tab {{
    background: transparent;
    color: {INK_SOFT};
    padding: 12px 20px;
    font-weight: 600;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{ color: {NAVY}; border-bottom: 2px solid {ACCENT}; }}
QTabBar::tab:hover {{ color: {NAVY}; }}

QFrame#card {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 10px;
}}
QLabel#cardTitle {{
    color: {INK_SOFT};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#fieldLabel {{ font-weight: 600; font-size: 12.5px; color: {INK}; }}
QLabel#fieldValue {{ color: {ACCENT}; font-weight: 700; font-size: 13px; }}

QSlider::groove:horizontal {{ height: 4px; background: {LINE}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::add-page:horizontal {{ background: {LINE}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}

QDoubleSpinBox, QSpinBox, QLineEdit {{
    background: {SURFACE_ALT};
    color: {INK};
    border: 1px solid {LINE};
    border-radius: 6px;
    padding: 6px 8px;
    min-height: 20px;
    font-weight: 600;
    selection-background-color: {ACCENT};
    selection-color: #FFFFFF;
}}
QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{ border: 1px solid {ACCENT}; }}

QPushButton#primaryBtn {{
    background: {ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 11px 22px;
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#primaryBtn:hover {{ background: {ACCENT_DARK}; }}
QPushButton#primaryBtn:disabled {{ background: {ACCENT_DISABLED}; }}

QPushButton#deleteBtn {{
    background: transparent;
    border: 1px solid {LINE};
    border-radius: 5px;
    color: {INK_SOFT};
    padding: 3px 12px;
    font-weight: 600;
}}
QPushButton#deleteBtn:hover {{ background: {DANGER_SOFT}; color: {DANGER}; border-color: {DANGER}; }}

QPushButton#showHideBtn {{
    background: {SURFACE_ALT};
    color: {INK_SOFT};
    border: 1px solid {LINE};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 20px;
    font-size: 11.5px;
    font-weight: 600;
}}
QPushButton#showHideBtn:hover {{ color: {INK}; border-color: {ACCENT}; }}

QFrame#statTile {{
    background: {SURFACE_ALT};
    border: 1px solid {LINE};
    border-radius: 8px;
}}
QLabel#statLabel {{ color: {INK_SOFT}; font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px; }}
QLabel#statValue {{ color: {NAVY}; font-size: 18px; font-weight: 700; }}

QTableWidget {{
    background: {SURFACE};
    border: none;
    gridline-color: {LINE};
    alternate-background-color: {SURFACE_ALT};
}}
QHeaderView::section {{
    background: {SURFACE_ALT};
    border: none;
    border-bottom: 1px solid {LINE};
    padding: 10px 8px;
    font-weight: 700;
    font-size: 10.5px;
    color: {INK_SOFT};
}}
QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {LINE}; }}

QLabel#statusLabel {{ color: {INK_SOFT}; font-size: 11.5px; }}
QLabel#emiHero {{ font-size: 13px; }}
"""


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(16)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(24)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(20, 40, 75, 28))
    frame.setGraphicsEffect(shadow)

    if title:
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)

    return frame, layout


def stat_tile(label_text: str) -> tuple[QFrame, QLabel]:
    tile = QFrame()
    tile.setObjectName("statTile")
    layout = QVBoxLayout(tile)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(6)

    label = QLabel(label_text.upper())
    label.setObjectName("statLabel")
    value = QLabel("—")
    value.setObjectName("statValue")

    layout.addWidget(label)
    layout.addWidget(value)
    return tile, value


def avatar_icon(letter: str, diameter: int = 28) -> QIcon:
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Helvetica Neue", int(diameter * 0.42))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter.upper())
    painter.end()
    return QIcon(pixmap)


def labeled_field(label_text: str, widget: QWidget) -> QVBoxLayout:
    """A label sitting tight above its own field, as one group — keeps a label
    unambiguously paired with its field regardless of how much space the
    surrounding layout puts between separate groups."""
    group = QVBoxLayout()
    group.setSpacing(6)
    label = QLabel(label_text)
    label.setObjectName("fieldLabel")
    group.addWidget(label)
    group.addWidget(widget)
    return group


class MainWindow(QMainWindow):
    def __init__(self, session: dict):
        super().__init__()
        self.session = session  # {"token", "username", "role", "loan_types"}
        self.tab_state = {}  # loan_type -> dict of widgets for that tab
        self.debounce_timers = {}

        self.setWindowTitle("EMI Estimator")
        self.setMinimumSize(960, 760)
        self.resize(1040, 820)

        self._build_ui()
        for loan_type in self.tab_state:
            self.refresh_preview(loan_type)
        self.refresh_history()

    # ---------------------------------------------------------------- UI ---
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 22, 28, 20)
        body_layout.setSpacing(14)
        root.addWidget(body, 1)

        tabs = QTabWidget()
        for loan_type in LOAN_TYPE_ORDER:
            if loan_type not in self.session["loan_types"]:
                continue
            config = LOAN_TYPE_CONFIG[loan_type]
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(150)
            timer.timeout.connect(lambda lt=loan_type: self.refresh_preview(lt))
            self.debounce_timers[loan_type] = timer
            tabs.addTab(self._build_loan_tab(loan_type, config), config["label"])

        if self.session["role"] == "admin":
            from .admin_window import AdminPanel

            tabs.addTab(AdminPanel(), "Admin")

        body_layout.addWidget(tabs, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        body_layout.addWidget(self.status_label)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 0, 28, 0)

        titles = QVBoxLayout()
        title = QLabel("EMI Estimator")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Royal Indraprastha Builders")
        subtitle.setObjectName("headerSubtitle")
        titles.addStretch(1)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        titles.addStretch(1)
        layout.addLayout(titles)

        layout.addStretch(1)

        username = self.session["username"]
        initial = (username[:1] or "?")

        account_btn = QToolButton()
        account_btn.setObjectName("accountBtn")
        account_btn.setText(username)
        account_btn.setIcon(avatar_icon(initial))
        account_btn.setIconSize(QSize(26, 26))
        account_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        account_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        account_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        menu = QMenu(account_btn)
        role_action = menu.addAction(self.session["role"].upper())
        role_action.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Change Password", self.on_change_password_clicked)
        account_btn.setMenu(menu)

        layout.addWidget(account_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        return header

    def on_change_password_clicked(self):
        from .change_password_window import ChangePasswordDialog

        dialog = ChangePasswordDialog(self)
        if dialog.exec() == ChangePasswordDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Password changed", "Your password has been updated.")

    def _build_loan_tab(self, loan_type: str, config: dict) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(18)

        calc_row = QHBoxLayout()
        calc_row.setSpacing(18)
        calc_row.addWidget(self._build_form_card(loan_type, config), 2)
        calc_row.addWidget(self._build_results_card(loan_type), 3)
        layout.addLayout(calc_row)

        layout.addWidget(self._build_history_card(loan_type), 1)
        return tab

    def _build_form_card(self, loan_type: str, config: dict) -> QFrame:
        frame, layout = card("LOAN DETAILS")
        state = self.tab_state.setdefault(loan_type, {})

        amt_min, amt_max, amt_default, amt_step = config["amount"]
        rate_min, rate_max, rate_default, rate_step = config["rate"]
        ten_min, ten_max, ten_default, ten_step = config["tenure"]

        state["amount_spin"] = self._build_field(
            layout, loan_type, "Loan amount (₹)", amt_min, amt_max, amt_default, amt_step, is_double=False
        )
        state["rate_spin"] = self._build_field(
            layout, loan_type, "Interest rate (% p.a.)", rate_min, rate_max, rate_default, rate_step, is_double=True
        )
        state["tenure_spin"] = self._build_field(
            layout, loan_type, "Tenure (years)", ten_min, ten_max, ten_default, ten_step, is_double=False
        )

        layout.addStretch(1)
        return frame

    def _build_field(self, parent_layout, loan_type, label_text, minimum, maximum, default, step, is_double):
        wrapper = QVBoxLayout()
        wrapper.setSpacing(8)

        head = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        value_label = QLabel("")
        value_label.setObjectName("fieldValue")
        head.addWidget(label)
        head.addStretch(1)
        head.addWidget(value_label)
        wrapper.addLayout(head)

        row = QHBoxLayout()
        row.setSpacing(10)
        slider = QSlider(Qt.Orientation.Horizontal)

        if is_double:
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            scale = 100
        else:
            spin = QSpinBox()
            scale = 1

        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setValue(default)
        spin.setFixedWidth(120)

        slider.setRange(int(minimum * scale), int(maximum * scale))
        slider.setSingleStep(int(step * scale))
        slider.setValue(int(default * scale))

        def sync_value_label():
            if is_double:
                value_label.setText(f"{spin.value():.2f}%")
            elif "amount" in label_text.lower():
                value_label.setText(format_inr(spin.value()))
            else:
                value_label.setText(f"{spin.value():.0f} yr")

        def on_slider_changed(v):
            spin.blockSignals(True)
            spin.setValue(v / scale)
            spin.blockSignals(False)
            sync_value_label()
            self.debounce_timers[loan_type].start()

        def on_spin_changed(v):
            slider.blockSignals(True)
            slider.setValue(int(v * scale))
            slider.blockSignals(False)
            sync_value_label()
            self.debounce_timers[loan_type].start()

        slider.valueChanged.connect(on_slider_changed)
        spin.valueChanged.connect(on_spin_changed)
        sync_value_label()

        row.addWidget(slider, 1)
        row.addWidget(spin)
        wrapper.addLayout(row)
        parent_layout.addLayout(wrapper)
        return spin

    def _build_results_card(self, loan_type: str) -> QFrame:
        frame, layout = card("MONTHLY EMI")
        state = self.tab_state[loan_type]

        emi_label = QLabel("₹0")
        emi_label.setObjectName("emiHero")
        emi_label.setTextFormat(Qt.TextFormat.RichText)
        state["emi_label"] = emi_label
        layout.addWidget(emi_label)

        bar_bar = QFrame()
        bar_bar.setFixedHeight(10)
        bar_bar.setStyleSheet(f"background: {LINE}; border-radius: 5px;")
        bar_layout = QHBoxLayout(bar_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        bar_principal = QFrame()
        bar_principal.setStyleSheet(f"background: {ACCENT}; border-top-left-radius: 5px; border-bottom-left-radius: 5px;")
        bar_interest = QFrame()
        bar_interest.setStyleSheet(f"background: {WARN}; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
        bar_layout.addWidget(bar_principal, 50)
        bar_layout.addWidget(bar_interest, 50)
        state["bar_bar"] = bar_bar
        layout.addWidget(bar_bar)

        legend = QHBoxLayout()
        principal_legend = QLabel(f'<span style="color:{ACCENT};">●</span> Principal —')
        interest_legend = QLabel(f'<span style="color:{WARN};">●</span> Interest —')
        state["principal_legend"] = principal_legend
        state["interest_legend"] = interest_legend
        legend.addWidget(principal_legend)
        legend.addSpacing(18)
        legend.addWidget(interest_legend)
        legend.addStretch(1)
        layout.addLayout(legend)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        interest_tile, total_interest_label = stat_tile("Total interest payable")
        payment_tile, total_payment_label = stat_tile("Total payment")
        state["total_interest_label"] = total_interest_label
        state["total_payment_label"] = total_payment_label
        stats_grid.addWidget(interest_tile, 0, 0)
        stats_grid.addWidget(payment_tile, 0, 1)
        layout.addLayout(stats_grid)

        save_row = QHBoxLayout()
        save_btn = QPushButton("Save to history")
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(lambda: self.on_save_clicked(loan_type))
        state["save_btn"] = save_btn
        save_row.addWidget(save_btn)
        save_row.addStretch(1)
        layout.addLayout(save_row)

        layout.addStretch(1)
        return frame

    def _build_history_card(self, loan_type: str) -> QFrame:
        frame, layout = card("")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        state = self.tab_state[loan_type]

        head = QHBoxLayout()
        head.setContentsMargins(22, 18, 22, 12)
        head_title = QLabel("Saved Calculations")
        head_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {NAVY};")
        history_count = QLabel("0 entries")
        history_count.setObjectName("statusLabel")
        state["history_count"] = history_count
        head.addWidget(head_title)
        head.addStretch(1)
        head.addWidget(history_count)
        layout.addLayout(head)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["SAVED", "AMOUNT", "RATE", "TENURE", "EMI", ""])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setMinimumHeight(180)
        state["table"] = table
        layout.addWidget(table, 1)

        return frame

    # ---------------------------------------------------------------- data ---
    def current_inputs(self, loan_type: str):
        state = self.tab_state[loan_type]
        return {
            "amount": float(state["amount_spin"].value()),
            "rate": float(state["rate_spin"].value()),
            "tenure_years": float(state["tenure_spin"].value()),
            "loan_type": loan_type,
        }

    def refresh_preview(self, loan_type: str):
        state = self.tab_state[loan_type]
        try:
            result = api_client.calculate_preview(**self.current_inputs(loan_type))
        except Exception as exc:
            self.status_label.setText(f"Backend unreachable — {exc}")
            state["save_btn"].setEnabled(False)
            return

        self.status_label.setText("")
        state["save_btn"].setEnabled(True)

        state["emi_label"].setText(
            f'<span style="font-size:36px; font-weight:800; color:{NAVY};">{format_inr(result["emi"])}</span>'
            f'<span style="font-size:13px; color:{INK_SOFT};"> / month</span>'
        )
        state["total_interest_label"].setText(format_inr(result["total_interest"]))
        state["total_payment_label"].setText(format_inr(result["total_payment"]))

        total = result["total_payment"] or 1
        principal_pct = (result["amount"] / total) * 100
        interest_pct = 100 - principal_pct
        bar_layout = state["bar_bar"].layout()
        bar_layout.setStretch(0, max(int(principal_pct), 1))
        bar_layout.setStretch(1, max(int(interest_pct), 1))
        state["principal_legend"].setText(f'<span style="color:{ACCENT};">●</span> Principal {principal_pct:.0f}%')
        state["interest_legend"].setText(f'<span style="color:{WARN};">●</span> Interest {interest_pct:.0f}%')

    def on_save_clicked(self, loan_type: str):
        try:
            api_client.save_calculation(**self.current_inputs(loan_type))
        except Exception as exc:
            QMessageBox.warning(self, "Could not save", str(exc))
            return
        self.refresh_history()

    def refresh_history(self):
        try:
            records = api_client.fetch_history()
        except Exception as exc:
            self.status_label.setText(f"Backend unreachable — {exc}")
            return

        by_type = {loan_type: [] for loan_type in self.tab_state}
        for record in records:
            if record["loan_type"] in by_type:
                by_type[record["loan_type"]].append(record)

        for loan_type, rows in by_type.items():
            state = self.tab_state[loan_type]
            table = state["table"]
            state["history_count"].setText(f"{len(rows)} {'entry' if len(rows) == 1 else 'entries'}")
            table.setRowCount(len(rows))
            for row, record in enumerate(rows):
                saved_at = record["created_at"][:16].replace("T", "  ")
                values = [
                    saved_at,
                    format_inr(record["amount"]),
                    f"{record['rate']:.2f}%",
                    f"{record['tenure_years']:.0f} yr",
                    format_inr(record["emi"]),
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col > 0:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    table.setItem(row, col, item)

                delete_btn = QPushButton("Delete")
                delete_btn.setObjectName("deleteBtn")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(lambda _, cid=record["id"]: self.on_delete_clicked(cid))
                table.setCellWidget(row, 5, delete_btn)

    def on_delete_clicked(self, calc_id: int):
        try:
            api_client.delete_calculation(calc_id)
        except Exception as exc:
            QMessageBox.warning(self, "Could not delete", str(exc))
            return
        self.refresh_history()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    from .login_window import LoginWindow

    login = LoginWindow()
    if login.exec() != LoginWindow.DialogCode.Accepted or login.session is None:
        sys.exit(0)

    window = MainWindow(login.session)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
