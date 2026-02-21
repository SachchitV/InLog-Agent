---
name: log-analysis
description: >
  This skill should be used when the user asks to "analyze", "parse",
  "infer", "structure", "schema", "read the log", "what format",
  "detect fields", "extract columns", "understand the log",
  "identify patterns", or any request about understanding or
  structuring a log file.
---

# Log Analysis & Parsing

Read raw timestamped log files, infer their schema, parse them into structured data, and store the results in SQLite.

## Workflow

1. Read the first 30-50 lines of the log file to understand its format.
2. Identify timestamp format, delimiters, and fields.
3. Write the inferred schema to `data/schemas/{file_id}.json`.
4. Present the schema to the user and wait for confirmation.
5. After confirmation, parse the full file and insert into SQLite.

## Schema Inference Pattern

```python
import json
import re

# Read sample lines
with open("data/uploads/{file_id}.log", "r") as f:
    sample_lines = [f.readline() for _ in range(50)]

# Analyze patterns — detect timestamp format, fields, delimiters
# Build schema JSON structure
schema = {
    "tables": [{
        "name": "events",
        "description": "Parsed log events",
        "columns": [
            {"name": "timestamp", "type": "TEXT", "description": "..."},
            # ... inferred columns ...
            {"name": "raw_line", "type": "TEXT", "description": "Original log line"}
        ]
    }],
    "timestamp_format": "...",
    "line_pattern": "...",
    "sample_parsed": [...]
}

# Write schema
with open("data/schemas/{file_id}.json", "w") as f:
    json.dump(schema, f, indent=2)
```

## Parsing & Storage Pattern

After schema is confirmed:

```python
import sqlite3
import re
import json
from datetime import datetime

# Load confirmed schema
with open("data/schemas/{file_id}.json", "r") as f:
    schema = json.load(f)

table = schema["tables"][0]
columns = table["columns"]
col_names = [c["name"] for c in columns]

# Create table
conn = sqlite3.connect("data/store.db")
cur = conn.cursor()
cur.execute(f"DROP TABLE IF EXISTS {table['name']}")

col_defs = ", ".join(f"{c['name']} {c['type']}" for c in columns)
cur.execute(f"CREATE TABLE {table['name']} ({col_defs})")

# Parse file
parsed = 0
failed = 0

with open("data/uploads/{file_id}.log", "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Apply regex pattern based on schema
        # Extract fields, convert types
        # Insert row
        parsed += 1

conn.commit()
conn.close()

print(f"Parsed {parsed} lines, {failed} failures")
```

### Critical Rules

- Always use `.venv/bin/python3` as the Python interpreter.
- Parser must use only stdlib: `re`, `datetime`, `json`.
- Use `sqlite3` for database operations.
- Always include `raw_line` column with the original log line.
- Store numeric values as numbers (INTEGER or REAL), not strings.
- Skip unparseable lines and count them — do not stop on failures.
- Drop and recreate the table if it already exists.
- Always connect to `data/store.db`.

## Schema Presentation

When presenting a schema to the user, format it clearly:

1. Show the table name and description.
2. List each column with its type and description.
3. Show the detected timestamp format and line pattern.
4. Include 2-3 sample parsed rows as examples.
5. Ask the user to confirm or request changes.

## Handling Schema Changes

When the user asks for modifications:

1. Read the current schema from `data/schemas/{file_id}.json`.
2. Apply the requested changes (add/remove/rename columns, change types).
3. Write the updated schema back.
4. Present the updated schema and wait for re-confirmation.
