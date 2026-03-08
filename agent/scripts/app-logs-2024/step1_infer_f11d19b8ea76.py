"""
Step 1 — Schema inference for f11d19b8ea76.log
Session: app-logs-2024

Adapted from scripts/app-logs-2024/step1_infer_ab405c100f0d.py (same log format).
"""
import sys
import json
import re
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.skills.lib.session import get_session_paths

SESSION_ID = "app-logs-2024"
FILE_ID = "f11d19b8ea76"

paths = get_session_paths(SESSION_ID)
log_path = Path(__file__).parent.parent.parent.parent / "data" / "uploads" / f"{FILE_ID}.log"
schema_path = Path(__file__).parent.parent.parent.parent / "data" / "schemas" / f"{FILE_ID}.json"

# Regex patterns
LOG_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|WARN|ERROR|DEBUG|CRITICAL)\s+"
    r"\[(?P<service>[^\]]+)\]\s+"
    r"(?P<message>.+)$"
)
GATEWAY_RE = re.compile(
    r"^(?P<http_method>GET|POST|PUT|DELETE|PATCH)\s+"
    r"(?P<http_path>\S+)\s+"
    r"(?P<http_status>\d{3})"
)
KV_RE = re.compile(r"(\w+)=([^\s]+)")

# Counters for field discovery
field_hits = {}
services = set()
levels = set()
parse_failures = 0

logger.info("Reading log file: %s", log_path)
with open(log_path) as f:
    lines = [l.rstrip("\n") for l in f if l.strip()]

total = len(lines)
for line in lines:
    m = LOG_RE.match(line)
    if not m:
        parse_failures += 1
        continue
    services.add(m.group("service"))
    levels.add(m.group("level"))
    msg = m.group("message")
    # Gateway fields
    gm = GATEWAY_RE.match(msg)
    if gm:
        for k in ("http_method", "http_path", "http_status"):
            field_hits[k] = field_hits.get(k, 0) + 1
    # Key=value extraction
    for k, v in KV_RE.findall(msg):
        field_hits[k] = field_hits.get(k, 0) + 1

logger.info("Total lines: %d  Parse failures: %d", total, parse_failures)
logger.info("Services found: %s", sorted(services))
logger.info("Levels found: %s", sorted(levels))
logger.info(
    "Key-value fields (by frequency): %s",
    sorted(field_hits.items(), key=lambda x: -x[1])
)

# ---- Build schema -------------------------------------------------------
# Core columns always present
columns = [
    {"name": "id",          "type": "INTEGER", "primary_key": True,  "description": "Auto-incrementing row ID"},
    {"name": "timestamp",   "type": "DATETIME","primary_key": False, "description": "Log event timestamp (YYYY-MM-DD HH:MM:SS)"},
    {"name": "level",       "type": "TEXT",    "primary_key": False, "description": "Log level: INFO | WARN | ERROR"},
    {"name": "service",     "type": "TEXT",    "primary_key": False, "description": "Originating service name"},
    {"name": "message",     "type": "TEXT",    "primary_key": False, "description": "Full message text after service tag"},
]

# Extracted structured columns
STRUCTURED = [
    # API gateway
    ("http_method",  "TEXT",    "HTTP verb from api-gateway lines (GET/POST/PUT/DELETE)"),
    ("http_path",    "TEXT",    "Request path from api-gateway lines"),
    ("http_status",  "INTEGER", "HTTP response status code"),
    ("latency_ms",   "INTEGER", "Request or query latency in milliseconds"),
    # Auth / session
    ("user",         "TEXT",    "Username involved in the event"),
    ("ip",           "TEXT",    "Client IP address"),
    ("session_id",   "TEXT",    "Session identifier"),
    # Business
    ("order_id",     "TEXT",    "Order identifier (e.g. ORD-10042)"),
    ("amount",       "REAL",    "Monetary amount for payments or refunds"),
    ("total",        "REAL",    "Order total amount"),
    ("error",        "TEXT",    "Error code or description"),
    # Infrastructure
    ("cpu",          "TEXT",    "CPU usage percentage string (e.g. 34%)"),
    ("memory",       "TEXT",    "Memory usage percentage string (e.g. 62%)"),
    ("disk",         "TEXT",    "Disk usage percentage string (e.g. 45%)"),
    ("active",       "INTEGER", "Active DB connections"),
    ("max",          "INTEGER", "Max DB connections configured"),
    # Always last
    ("raw_line",     "TEXT",    "Original unparsed log line"),
]
for name, typ, desc in STRUCTURED:
    columns.append({"name": name, "type": typ, "primary_key": False, "description": desc})

schema = {
    "file_id": FILE_ID,
    "filename": f"{FILE_ID}.log",
    "inferred_at": datetime.utcnow().isoformat(),
    "log_format": "DATETIME LEVEL [SERVICE] MESSAGE [key=value ...]",
    "timestamp_format": "%Y-%m-%d %H:%M:%S",
    "delimiter": "space",
    "total_lines": total,
    "parse_failures": parse_failures,
    "services": sorted(services),
    "levels": sorted(levels),
    "kv_field_hits": dict(sorted(field_hits.items(), key=lambda x: -x[1])),
    "table": {
        "name": "logs_f11d19b8ea76",
        "columns": columns,
    },
    "notes": [
        "api-gateway lines embed HTTP method, path, and status code at the start of the message",
        "Key-value pairs (key=value) are extracted into dedicated columns where applicable",
        "Unparseable lines are skipped and counted in parse_failures",
        "cpu/memory/disk stored as TEXT to preserve the % suffix from health-check lines",
    ],
}

schema_path.parent.mkdir(parents=True, exist_ok=True)
with open(schema_path, "w") as f:
    json.dump(schema, f, indent=2)
logger.info("Schema written to %s", schema_path)
