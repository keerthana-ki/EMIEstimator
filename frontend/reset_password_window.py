from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from . import api_client
from .app import DANGER, INK_SOFT, NAVY, labeled_field


class ResetPasswordDialog(QDialog):
    def __init__(self, user_id: int, username: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username
        self.setWindowTitle("Reset Password")
        self.setFixedSize(340, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Reset Password")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {NAVY};")
        subtitle = QLabel(f'Setting a new password for "{self.username}"')
        subtitle.setStyleSheet(f"font-size: 11.5px; color: {INK_SOFT}; margin-bottom: 4px;")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(4)

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
        submit_btn = QPushButton("Reset password")
        submit_btn.setObjectName("primaryBtn")
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(submit_btn)

        layout.addStretch(1)

    def _on_submit(self):
        new = self.new_input.text()
        confirm = self.confirm_input.text()

        if not new:
            self._show_error("Enter a new password.")
            return
        if new != confirm:
            self._show_error("Passwords don't match.")
            return

        try:
            api_client.admin_reset_password(self.user_id, new)
        except Exception as exc:
            self._show_error(f"Could not reset password — {exc}")
            return

        self.accept()

    def _show_error(self, text: str):
        self.error_label.setText(text)
        self.error_label.show()
