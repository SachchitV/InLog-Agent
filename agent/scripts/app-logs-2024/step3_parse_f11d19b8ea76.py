"""
Step 3: Parse f11d19b8ea76.log and load into SQLite.
Schema: DATETIME LEVEL [SERVICE] MESSAGE [key=value ...]
"""
import sys
import re
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Bootstrap path so we can import skills
# ---------------------------------------------------------------------------
AGENT_DIR = Path(__file__).resolve().parent.parent.parent  # → agent/
sys.path.insert(0, str(AGENT_DIR))
from code.skills.lib.session import get_session_paths

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SESSION_ID  = "app-logs-2024"
FILE_ID     = "f11d19b8ea76"
paths       = get_session_paths(SESSION_ID)

LOG_FILE    = AGENT_DIR.parent / "data" / "uploads" / f"{FILE_ID}.log"
SCHEMA_FILE = AGENT_DIR.parent / "data" / "schemas" / f"{FILE_ID}.json"
DB_PATH     = AGENT_DIR.parent / "data" / "store.db"
TABLE       = f"logs_{FILE_ID}"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r"\s+(?P<level>INFO|WARN|ERROR)"
    r"\s+\[(?P<service>[^\]]+)\]"
    r"\s+(?P<rest>.+)$"
)
KV_RE = re.compile(r"(\w+)=([^\s]+)")


def parse_kv(text: str) -> dict:
    """Extract key=value pairs from a string."""
    return {k: v for k, v in KV_RE.findall(text)}


def coerce(value: str, column: str, col_types: dict):
    """Cast a string value to the appropriate Python type."""
    if value is None:
        return None
    col_type = col_types.get(column, "TEXT")
    try:
        if col_type == "INTEGER":
            return int(value)
        if col_type == "REAL":
            return float(value)
    except (ValueError, TypeError):
        pass
    return value


def parse_line(raw: str, col_types: dict) -> dict | None:
    """Parse a single log line into a dict matching the schema columns."""
    raw = raw.rstrip("\n")
    m = LINE_RE.match(raw)
    if not m:
        return None

    row = {
        "timestamp":   m.group("timestamp"),
        "level":       m.group("level"),
        "service":     m.group("service"),
        "message":     m.group("rest"),
        "raw_line":    raw,
        # numeric / text columns start as None
        "http_method": None, "http_path": None, "http_status": None,
        "latency_ms":  None, "user":       None, "ip":          None,
        "session_id":  None, "order_id":   None, "amount":      None,
        "total":       None, "error":      None, "cpu":         None,
        "memory":      None, "disk":       None, "active":      None,
        "max":         None,
    }

    rest = m.group("rest")
    kv   = parse_kv(rest)

    # Populate known kv columns
    for col in ("http_method", "http_path", "http_status", "latency_ms",
                 "user", "ip", "session_id", "order_id", "amount", "total",
                 "error", "cpu", "memory", "disk", "active", "max"):
        if col in kv:
            row[col] = coerce(kv[col], col, col_types)

    return row


def main():
    log.info("Loading schema from %s", SCHEMA_FILE)
    schema = json.loads(SCHEMA_FILE.read_text())
    col_types = {c["name"]: c["type"] for c in schema["table"]["columns"]}

    log.info("Parsing log file: %s", LOG_FILE)
    lines     = LOG_FILE.read_text(encoding="utf-8").splitlines()
    rows      = []
    failures  = 0

    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        row = parse_line(raw, col_types)
        if row is None:
            log.warning("Parse failure at line %d: %s", i, raw[:120])
            failures += 1
        else:
            rows.append(row)

    log.info("Parsed %d rows, %d failures out of %d lines", len(rows), failures, len(lines))

    # ------------------------------------------------------------------
    # Load into SQLite
    # ------------------------------------------------------------------
    log.info("Connecting to database: %s", DB_PATH)
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
    cur.execute(f"""
        CREATE TABLE {TABLE} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   DATETIME,
            level       TEXT,
            service     TEXT,
            message     TEXT,
            http_method TEXT,
            http_path   TEXT,
            http_status INTEGER,
            latency_ms  INTEGER,
            user        TEXT,
            ip          TEXT,
            session_id  TEXT,
            order_id    TEXT,
            amount      REAL,
            total       REAL,
            error       TEXT,
            cpu         TEXT,
            memory      TEXT,
            disk        TEXT,
            active      INTEGER,
            max         INTEGER,
            raw_line    TEXT
        )
    """)

    columns = ["timestamp","level","service","message","http_method",
               "http_path","http_status","latency_ms","user","ip",
               "session_id","order_id","amount","total","error",
               "cpu","memory","disk","active","max","raw_line"]
    placeholders = ",".join("?" * len(columns))
    col_list = ",".join(columns)

    cur.executemany(
        f"INSERT INTO {TABLE} ({col_list}) VALUES ({placeholders})",
        [[r[c] for c in columns] for r in rows],
    )
    con.commit()

    count = cur.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    log.info("Inserted %d rows into table '%s'", count, TABLE)

    # Quick sanity: level breakdown
    for level, n in cur.execute(
        f"SELECT level, COUNT(*) FROM {TABLE} GROUP BY level ORDER BY level"
    ):
        log.info("  %-5s : %d", level, n)

    con.close()
    log.info("Done.")
    return count, failures


if __name__ == "__main__":
    main()
