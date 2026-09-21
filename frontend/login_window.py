import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from . import api_client
from .app import DANGER, INK_SOFT, NAVY, NAVY_SOFT


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.session = None

        self.setWindowTitle("EMI Estimator — Log In")
        self.setFixedSize(380, 420)
        self._build_ui()
        self._check_bootstrap()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 28)
        layout.setSpacing(10)

        title = QLabel("EMI Estimator")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {NAVY};")
        subtitle = QLabel("Royal Indraprastha Builders")
        subtitle.setStyleSheet(f"font-size: 11.5px; color: {INK_SOFT}; margin-bottom: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.bootstrap_label = QLabel("")
        self.bootstrap_label.setWordWrap(True)
        self.bootstrap_label.setStyleSheet(
            f"background: #EEF3FB; color: {NAVY}; border: 1px solid {NAVY_SOFT}; "
            "border-radius: 6px; padding: 10px; font-size: 11.5px;"
        )
        self.bootstrap_label.hide()
        layout.addWidget(self.bootstrap_label)

        layout.addSpacing(6)
        layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._on_login_clicked)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {DANGER}; font-size: 11.5px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addSpacing(6)
        self.login_btn = QPushButton("Log in")
        self.login_btn.setObjectName("primaryBtn")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_btn)

        layout.addStretch(1)

    def _check_bootstrap(self):
        try:
            status = api_client.get_bootstrap_status()
        except Exception:
            return
        if status.get("just_created"):
            self.bootstrap_label.setText(
                f"First run — an admin account was just created.\n\n"
                f"Username: {status['username']}\n"
                f"Password: {status['password']}\n\n"
                f"Log in and create real accounts from the Admin tab."
            )
            self.bootstrap_label.show()

    def _on_login_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self._show_error("Enter both a username and a password.")
            return

        self.login_btn.setEnabled(False)
        try:
            data = api_client.login(username, password)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                self._show_error("Invalid username or password.")
            else:
                self._show_error(f"Login failed — {exc}")
        except Exception as exc:
            self._show_error(f"Could not reach the server — {exc}")
        else:
            self.session = data
            self.accept()
            return
        finally:
            self.login_btn.setEnabled(True)

    def _show_error(self, text: str):
        self.error_label.setText(text)
        self.error_label.show()
