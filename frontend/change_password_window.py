import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from . import api_client
from .app import DANGER, NAVY, labeled_field


class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setFixedSize(340, 340)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Change Password")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {NAVY};")
        layout.addWidget(title)
        layout.addSpacing(6)

        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addLayout(labeled_field("Current password", self.current_input))

        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addLayout(labeled_field("New password", self.new_input))

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.returnPressed.connect(self._on_submit)
        layout.addLayout(labeled_field("Confirm new password", self.confirm_input))

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {DANGER}; font-size: 11.5px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addSpacing(4)
        submit_btn = QPushButton("Change password")
        submit_btn.setObjectName("primaryBtn")
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(submit_btn)

        layout.addStretch(1)

    def _on_submit(self):
        current = self.current_input.text()
        new = self.new_input.text()
        confirm = self.confirm_input.text()

        if not current or not new:
            self._show_error("Fill in both your current and new password.")
            return
        if new != confirm:
            self._show_error("New password and confirmation don't match.")
            return

        try:
            api_client.change_password(current, new)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                self._show_error("Current password is incorrect.")
            else:
                self._show_error(f"Could not change password — {exc}")
            return
        except Exception as exc:
            self._show_error(f"Could not reach the server — {exc}")
            return

        self.accept()

    def _show_error(self, text: str):
        self.error_label.setText(text)
        self.error_label.show()
