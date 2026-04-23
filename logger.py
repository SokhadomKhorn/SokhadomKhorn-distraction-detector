from datetime import datetime
from pathlib import Path


LOG_FILE = Path(__file__).resolve().parent / "distracted_alerts.log"


def log_distracted_alert(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as file_handle:
        file_handle.write(f"[{timestamp}] {message}\n")