from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOG_FILE = BASE_DIR / "distracted_alerts.log"

app = Flask(__name__)


@dataclass
class SessionSummary:
    start: str
    end: str
    alerts: int
    duration_seconds: int


def parse_alert_entries(log_text: str) -> list[datetime]:
    entries: list[datetime] = []
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith("[") or "]" not in line:
            continue
        timestamp_text = line.split("]", 1)[0].lstrip("[")
        try:
            entries.append(datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            continue
    return entries


def build_sessions(entries: list[datetime], gap_threshold_seconds: int = 60) -> list[SessionSummary]:
    if not entries:
        return []

    sessions: list[list[datetime]] = []
    current_session = [entries[0]]
    for previous_entry, current_entry in zip(entries, entries[1:]):
        if (current_entry - previous_entry).total_seconds() > gap_threshold_seconds:
            sessions.append(current_session)
            current_session = [current_entry]
        else:
            current_session.append(current_entry)
    sessions.append(current_session)

    summaries: list[SessionSummary] = []
    for session in sessions:
        session_start = session[0]
        session_end = session[-1]
        summaries.append(
            SessionSummary(
                start=session_start.strftime("%Y-%m-%d %H:%M:%S"),
                end=session_end.strftime("%Y-%m-%d %H:%M:%S"),
                alerts=len(session),
                duration_seconds=int((session_end - session_start).total_seconds()),
            )
        )
    return summaries


def build_analytics(entries: list[datetime]) -> dict:
    if not entries:
        return {
            "total_alerts": 0,
            "first_alert": None,
            "last_alert": None,
            "span_text": "0 seconds",
            "avg_gap_text": "N/A",
            "min_gap_text": "N/A",
            "max_gap_text": "N/A",
            "hour_labels": [],
            "hour_counts": [],
            "sessions": [],
        }

    entries = sorted(entries)
    intervals = [(current - previous).total_seconds() for previous, current in zip(entries, entries[1:])]
    total_span_seconds = int((entries[-1] - entries[0]).total_seconds())
    hour_counts = Counter(entry.strftime("%H:00") for entry in entries)
    hour_labels = sorted(hour_counts.keys())

    sessions = build_sessions(entries)

    return {
        "total_alerts": len(entries),
        "first_alert": entries[0].strftime("%Y-%m-%d %H:%M:%S"),
        "last_alert": entries[-1].strftime("%Y-%m-%d %H:%M:%S"),
        "span_text": f"{total_span_seconds // 60} minutes {total_span_seconds % 60} seconds",
        "avg_gap_text": f"{sum(intervals) / len(intervals):.1f} seconds" if intervals else "N/A",
        "min_gap_text": f"{min(intervals):.0f} seconds" if intervals else "N/A",
        "max_gap_text": f"{max(intervals):.0f} seconds" if intervals else "N/A",
        "hour_labels": hour_labels,
        "hour_counts": [hour_counts[label] for label in hour_labels],
        "sessions": sessions,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    source_name = DEFAULT_LOG_FILE.name
    if DEFAULT_LOG_FILE.exists():
        log_text = DEFAULT_LOG_FILE.read_text(encoding="utf-8", errors="ignore")
    else:
        log_text = ""

    entries = parse_alert_entries(log_text)
    analytics = build_analytics(entries)

    return render_template(
        "index.html",
        source_name=source_name,
        analytics=analytics,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
