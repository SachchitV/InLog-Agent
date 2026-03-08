"""
Step 4: Generate overview charts for f11d19b8ea76 log data.

Charts produced:
  1. log_level_distribution.png   – Pie chart of INFO / WARN / ERROR counts
  2. events_per_service.png       – Horizontal bar chart of event count by service
  3. event_timeline.png           – Events over time, stacked by level
  4. latency_by_service.png       – Average & max latency per service (gateway only)
  5. http_status_distribution.png – HTTP status code breakdown
"""
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
AGENT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AGENT_DIR))
from code.skills.lib.session import get_session_paths

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SESSION_ID = "app-logs-2024"
FILE_ID    = "f11d19b8ea76"
TABLE      = f"logs_{FILE_ID}"
DB_PATH    = AGENT_DIR.parent / "data" / "store.db"
OUT_DIR    = AGENT_DIR.parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Colour palette
LEVEL_COLORS = {"INFO": "#4C9BE8", "WARN": "#F4A62A", "ERROR": "#E84C4C"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def query(con, sql, params=()):
    cur = con.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def savefig(fig, name: str):
    path = OUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved chart → %s", path)


# ---------------------------------------------------------------------------
# Chart 1: Log-level distribution (pie)
# ---------------------------------------------------------------------------
def chart_level_distribution(con):
    rows = query(con, f"SELECT level, COUNT(*) AS n FROM {TABLE} GROUP BY level ORDER BY level")
    labels = [r["level"] for r in rows]
    sizes  = [r["n"]     for r in rows]
    colors = [LEVEL_COLORS.get(l, "#aaaaaa") for l in labels]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=140, textprops={"fontsize": 12}
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_fontweight("bold")
    ax.set_title("Log Level Distribution", fontsize=15, fontweight="bold", pad=15)
    savefig(fig, "log_level_distribution.png")


# ---------------------------------------------------------------------------
# Chart 2: Events per service (horizontal bar)
# ---------------------------------------------------------------------------
def chart_events_per_service(con):
    rows = query(con,
        f"SELECT service, COUNT(*) AS n FROM {TABLE} GROUP BY service ORDER BY n DESC")
    services = [r["service"] for r in rows]
    counts   = [r["n"]       for r in rows]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(services[::-1], counts[::-1], color="#4C9BE8", edgecolor="white")
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_xlabel("Number of Events", fontsize=11)
    ax.set_title("Events per Service", fontsize=15, fontweight="bold")
    ax.set_xlim(0, max(counts) * 1.18)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    savefig(fig, "events_per_service.png")


# ---------------------------------------------------------------------------
# Chart 3: Event timeline – events per minute, stacked by level
# ---------------------------------------------------------------------------
def chart_event_timeline(con):
    rows = query(con,
        f"SELECT strftime('%Y-%m-%d %H:%M', timestamp) AS minute, level, COUNT(*) AS n "
        f"FROM {TABLE} GROUP BY minute, level ORDER BY minute")

    buckets = defaultdict(lambda: {"INFO": 0, "WARN": 0, "ERROR": 0})
    for r in rows:
        buckets[r["minute"]][r["level"]] = r["n"]

    minutes = sorted(buckets.keys())
    times   = [datetime.strptime(m, "%Y-%m-%d %H:%M") for m in minutes]
    info_v  = [buckets[m]["INFO"]  for m in minutes]
    warn_v  = [buckets[m]["WARN"]  for m in minutes]
    error_v = [buckets[m]["ERROR"] for m in minutes]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(times, info_v,  label="INFO",  color=LEVEL_COLORS["INFO"],  width=0.0005)
    ax.bar(times, warn_v,  label="WARN",  color=LEVEL_COLORS["WARN"],  width=0.0005,
           bottom=info_v)
    ax.bar(times, error_v, label="ERROR", color=LEVEL_COLORS["ERROR"], width=0.0005,
           bottom=[i+w for i, w in zip(info_v, warn_v)])

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate(rotation=45)
    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("Events", fontsize=11)
    ax.set_title("Event Timeline (per Minute)", fontsize=15, fontweight="bold")
    ax.legend(framealpha=0.8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    savefig(fig, "event_timeline.png")


# ---------------------------------------------------------------------------
# Chart 4: Latency by service (avg + max, for rows with latency_ms)
# ---------------------------------------------------------------------------
def chart_latency_by_service(con):
    rows = query(con,
        f"SELECT service, AVG(latency_ms) AS avg_ms, MAX(latency_ms) AS max_ms, COUNT(*) AS n "
        f"FROM {TABLE} WHERE latency_ms IS NOT NULL "
        f"GROUP BY service ORDER BY avg_ms DESC")

    if not rows:
        log.info("No latency data – skipping latency chart.")
        return

    services = [r["service"] for r in rows]
    avgs     = [round(r["avg_ms"], 1) for r in rows]
    maxes    = [r["max_ms"] for r in rows]

    x = range(len(services))
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.35
    b1 = ax.bar([i - width/2 for i in x], avgs,  width, label="Avg latency",
                color="#4C9BE8", edgecolor="white")
    b2 = ax.bar([i + width/2 for i in x], maxes, width, label="Max latency",
                color="#E84C4C", edgecolor="white")
    ax.bar_label(b1, fmt="%.0f", padding=3, fontsize=8)
    ax.bar_label(b2, fmt="%.0f", padding=3, fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(services, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_title("Avg & Max Latency by Service", fontsize=15, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    savefig(fig, "latency_by_service.png")


# ---------------------------------------------------------------------------
# Chart 5: HTTP status distribution (for rows that have http_status)
# ---------------------------------------------------------------------------
def chart_http_status(con):
    rows = query(con,
        f"SELECT http_status, COUNT(*) AS n FROM {TABLE} "
        f"WHERE http_status IS NOT NULL GROUP BY http_status ORDER BY http_status")

    if not rows:
        log.info("No HTTP status data – skipping.")
        return

    def status_color(s):
        if s < 300: return "#4C9BE8"
        if s < 400: return "#63C47E"
        if s < 500: return "#F4A62A"
        return "#E84C4C"

    statuses = [str(r["http_status"]) for r in rows]
    counts   = [r["n"] for r in rows]
    colors   = [status_color(r["http_status"]) for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(statuses, counts, color=colors, edgecolor="white")
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_xlabel("HTTP Status Code", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("HTTP Response Status Distribution", fontsize=15, fontweight="bold")
    ax.set_ylim(0, max(counts) * 1.2)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Legend patches
    import matplotlib.patches as mpatches
    legend_items = [
        mpatches.Patch(color="#4C9BE8", label="2xx Success"),
        mpatches.Patch(color="#63C47E", label="3xx Redirect"),
        mpatches.Patch(color="#F4A62A", label="4xx Client error"),
        mpatches.Patch(color="#E84C4C", label="5xx Server error"),
    ]
    ax.legend(handles=legend_items, fontsize=9)
    fig.tight_layout()
    savefig(fig, "http_status_distribution.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("Connecting to %s", DB_PATH)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    chart_level_distribution(con)
    chart_events_per_service(con)
    chart_event_timeline(con)
    chart_latency_by_service(con)
    chart_http_status(con)

    con.close()
    log.info("All charts generated.")


if __name__ == "__main__":
    main()
