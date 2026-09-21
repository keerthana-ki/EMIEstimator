"""Launches the FastAPI backend (background thread) and the PyQt6 desktop UI (main thread).

The frontend and backend only ever talk over HTTP (see frontend/api_client.py) — this
launcher just starts both processes together for convenience. Run the backend on its
own with `uvicorn backend.main:app --port 8731` if you ever want the API without the UI.
"""
import threading
import time

import requests
import uvicorn

from backend.main import app as backend_app
from frontend.app import main as run_frontend

HOST = "127.0.0.1"
PORT = 8731


def run_backend():
    uvicorn.run(backend_app, host=HOST, port=PORT, log_level="warning")


def wait_for_backend(timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"http://{HOST}:{PORT}/calculations", timeout=1)
            return True
        except Exception:
            time.sleep(0.15)
    return False


def main():
    server_thread = threading.Thread(target=run_backend, daemon=True)
    server_thread.start()

    if not wait_for_backend():
        print("Backend did not start in time — the app will show a connection error.")

    run_frontend()


if __name__ == "__main__":
    main()
