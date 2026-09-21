from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import api_client
from .app import DANGER, card, labeled_field

LOAN_TYPE_COLUMNS = [("home", "Home Loan"), ("car", "Car Loan")]
RESET_COL_WIDTH = 140
DELETE_COL_WIDTH = 80


class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 18, 0, 0)
        root.setSpacing(18)

        top_row = QHBoxLayout()
        top_row.setSpacing(18)
        top_row.addWidget(self._build_create_card(), 1, Qt.AlignmentFlag.AlignTop)
        top_row.addWidget(self._build_users_card(), 2)
        root.addLayout(top_row)

        root.addWidget(self._build_log_card())

        self.refresh_users()
        self.refresh_log()

    def _build_create_card(self):
        frame, layout = card("CREATE USER")
        layout.setSpacing(0)  # every gap below is explicit — nothing implicit left to verify

        FIELD_HEIGHT = 34
        GROUP_GAP = 22  # between one labeled field-group and the next

        self.username_input = QLineEdit()
        self.username_input.setFixedHeight(FIELD_HEIGHT)
        layout.addLayout(labeled_field("Username", self.username_input))
        layout.addSpacing(GROUP_GAP)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(FIELD_HEIGHT)

        self.password_toggle_btn = QPushButton("Show")
        self.password_toggle_btn.setObjectName("showHideBtn")
        self.password_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.password_toggle_btn.setFixedSize(58, FIELD_HEIGHT)
        self.password_toggle_btn.clicked.connect(self._toggle_password_visibility)

        password_container = QWidget()
        password_container.setFixedHeight(FIELD_HEIGHT + 8)
        password_row = QHBoxLayout(password_container)
        password_row.setContentsMargins(0, 0, 0, 0)
        password_row.setSpacing(8)
        password_row.addWidget(self.password_input, 1, Qt.AlignmentFlag.AlignVCenter)
        password_row.addWidget(self.password_toggle_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(labeled_field("Temporary password", password_container))
        layout.addSpacing(GROUP_GAP)

        loan_access_label = QLabel("Loan access")
        loan_access_label.setObjectName("fieldLabel")
        layout.addWidget(loan_access_label)
        layout.addSpacing(8)
        self.new_user_checks = {}
        for index, (loan_type, label) in enumerate(LOAN_TYPE_COLUMNS):
            box = QCheckBox(label)
            self.new_user_checks[loan_type] = box
            layout.addWidget(box)
            if index < len(LOAN_TYPE_COLUMNS) - 1:
                layout.addSpacing(6)
        layout.addSpacing(GROUP_GAP)

        self.create_error_label = QLabel("")
        self.create_error_label.setStyleSheet(f"color: {DANGER}; font-size: 11.5px;")
        self.create_error_label.setWordWrap(True)
        self.create_error_label.hide()
        layout.addWidget(self.create_error_label)
        layout.addSpacing(10)

        create_btn = QPushButton("Create user")
        create_btn.setObjectName("primaryBtn")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self.on_create_clicked)
        layout.addWidget(create_btn)

        return frame

    def _build_users_card(self):
        frame, layout = card("USERS")

        reset_col = 2 + len(LOAN_TYPE_COLUMNS)
        delete_col = reset_col + 1
        self.table = QTableWidget(0, delete_col + 1)
        headers = ["USERNAME", "ROLE"] + [label.upper() for _, label in LOAN_TYPE_COLUMNS] + ["", ""]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(reset_col, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(delete_col, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(reset_col, RESET_COL_WIDTH)
        self.table.setColumnWidth(delete_col, DELETE_COL_WIDTH)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        layout.addWidget(self.table, 1)
        return frame

    def _build_log_card(self):
        frame, layout = card("RECENT PASSWORD CHANGES")

        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["WHEN", "ACCOUNT", "CHANGED BY"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setShowGrid(False)
        self.log_table.setMinimumHeight(160)
        layout.addWidget(self.log_table, 1)
        return frame

    def on_create_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        loan_types = [lt for lt, box in self.new_user_checks.items() if box.isChecked()]

        if not username or not password:
            self._show_create_error("Enter a username and a temporary password.")
            return
        if not loan_types:
            self._show_create_error("Grant access to at least one loan type.")
            return

        try:
            api_client.create_user(username, password, loan_types)
        except Exception as exc:
            self._show_create_error(f"Could not create user — {exc}")
            return

        self.create_error_label.hide()
        self.username_input.clear()
        self.password_input.clear()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_toggle_btn.setText("Show")
        for box in self.new_user_checks.values():
            box.setChecked(False)
        self.refresh_users()

    def _toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_toggle_btn.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle_btn.setText("Show")

    def _show_create_error(self, text: str):
        self.create_error_label.setText(text)
        self.create_error_label.show()

    def refresh_users(self):
        try:
            users = api_client.list_users()
        except Exception as exc:
            QMessageBox.warning(self, "Could not load users", str(exc))
            return

        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user["username"]))
            self.table.setItem(row, 1, QTableWidgetItem(user["role"]))

            is_admin = user["role"] == "admin"
            for col_offset, (loan_type, _label) in enumerate(LOAN_TYPE_COLUMNS):
                checkbox = QCheckBox()
                checkbox.setChecked(is_admin or loan_type in user["loan_types"])
                checkbox.setEnabled(not is_admin)
                if not is_admin:
                    checkbox.stateChanged.connect(
                        lambda _state, uid=user["id"], row=row: self._on_permission_toggled(uid, row)
                    )
                cell = QWidget()
                cell_layout = QHBoxLayout(cell)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignCenter)
                self.table.setCellWidget(row, 2 + col_offset, cell)

            reset_col = 2 + len(LOAN_TYPE_COLUMNS)
            delete_col = reset_col + 1

            reset_btn = QPushButton("Reset Password")
            reset_btn.setObjectName("deleteBtn")
            reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            reset_btn.clicked.connect(
                lambda _, uid=user["id"], uname=user["username"]: self.on_reset_password_clicked(uid, uname)
            )
            self.table.setCellWidget(row, reset_col, reset_btn)

            if is_admin:
                self.table.setCellWidget(row, delete_col, QWidget())
            else:
                delete_btn = QPushButton("Delete")
                delete_btn.setObjectName("deleteBtn")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(
                    lambda _, uid=user["id"], uname=user["username"]: self.on_delete_clicked(uid, uname)
                )
                self.table.setCellWidget(row, delete_col, delete_btn)

    def refresh_log(self):
        try:
            entries = api_client.get_password_log()
        except Exception:
            return

        self.log_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            when = entry["changed_at"][:16].replace("T", "  ")
            changed_by = entry["changed_by_username"]
            if entry["changed_by_username"] == entry["target_username"]:
                changed_by += " (self)"
            for col, value in enumerate([when, entry["target_username"], changed_by]):
                self.log_table.setItem(row, col, QTableWidgetItem(value))

    def on_delete_clicked(self, user_id: int, username: str):
        confirm = QMessageBox.question(
            self,
            "Delete user",
            f'Delete "{username}"? This cannot be undone — their login will stop working immediately.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            api_client.delete_user(user_id)
        except Exception as exc:
            QMessageBox.warning(self, "Could not delete user", str(exc))
            return

        self.refresh_users()

    def on_reset_password_clicked(self, user_id: int, username: str):
        from .reset_password_window import ResetPasswordDialog

        dialog = ResetPasswordDialog(user_id, username, self)
        if dialog.exec() == ResetPasswordDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Password reset", f'Password for "{username}" has been updated.')
            self.refresh_log()

    def _on_permission_toggled(self, user_id: int, row: int):
        loan_types = []
        for col_offset, (loan_type, _label) in enumerate(LOAN_TYPE_COLUMNS):
            cell = self.table.cellWidget(row, 2 + col_offset)
            checkbox = cell.findChild(QCheckBox)
            if checkbox.isChecked():
                loan_types.append(loan_type)
        try:
            api_client.update_user_permissions(user_id, loan_types)
        except Exception as exc:
            QMessageBox.warning(self, "Could not update permissions", str(exc))
            self.refresh_users()
