---
name: log-viz
description: >
  This skill should be used when the user asks to "chart", "plot",
  "visualize", "trend", "graph", "show me a chart", "timeline",
  "distribution", "histogram", "bar chart", "line chart",
  "show errors over time", "frequency", or any request about
  creating visual representations of parsed log data.
---

# Log Data Visualization

Generate publication-quality charts from parsed log data stored in SQLite.

## Setup Requirements

Every visualization script must configure matplotlib for headless rendering before importing pyplot:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```

This is mandatory — the execution environment has no display server.

## Execution Pattern

```python
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid')

conn = sqlite3.connect("data/store.db")
df = pd.read_sql_query("SELECT ... FROM events ...", conn)
conn.close()

fig, ax = plt.subplots(figsize=(10, 6))
# ... plot code ...

ax.set_title("Chart Title", fontsize=14, fontweight='bold')
ax.set_xlabel("X Label")
ax.set_ylabel("Y Label")

plt.tight_layout()
plt.savefig("outputs/descriptive_name.png", dpi=150, bbox_inches='tight')
plt.close()

print("Chart saved to outputs/descriptive_name.png")
```

### Critical Rules

- Always use `.venv/bin/python3` as the Python interpreter.
- Always call `matplotlib.use('Agg')` before importing `pyplot`.
- Always use `plt.style.use('seaborn-v0_8-whitegrid')` for consistent styling.
- Always call `plt.tight_layout()` before saving.
- Always save to the `outputs/` directory with a descriptive filename.
- Always use `dpi=150` for clear, readable output.
- Always call `plt.close()` after saving to free memory.
- Always print the output path so the system can track generated files.

## Common Chart Types for Log Data

### Timeline / Events Over Time

```python
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp').resample('1h').size().plot(ax=ax)
ax.set_title("Events Over Time")
ax.set_ylabel("Event Count")
```

### Log Level Distribution

```python
level_counts = df['level'].value_counts()
colors = {'ERROR': '#e74c3c', 'WARN': '#f39c12', 'INFO': '#3498db', 'DEBUG': '#95a5a6'}
level_counts.plot(kind='bar', ax=ax, color=[colors.get(l, '#3498db') for l in level_counts.index])
ax.set_title("Log Level Distribution")
ax.set_ylabel("Count")
```

### Error Rate Over Time

```python
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['is_error'] = df['level'] == 'ERROR'
error_rate = df.set_index('timestamp').resample('1h')['is_error'].mean() * 100
error_rate.plot(ax=ax, color='#e74c3c')
ax.set_title("Error Rate Over Time")
ax.set_ylabel("Error Rate (%)")
```

### Top Sources / Components

```python
top_sources = df['source'].value_counts().head(10)
top_sources.plot(kind='barh', ax=ax)
ax.set_title("Top 10 Log Sources")
ax.set_xlabel("Event Count")
```

## Color Palette

Use consistent colors for log levels:
- ERROR: `#e74c3c` (red)
- WARN / WARNING: `#f39c12` (orange)
- INFO: `#3498db` (blue)
- DEBUG: `#95a5a6` (gray)
- CRITICAL / FATAL: `#8e44ad` (purple)

## File Naming Convention

Use descriptive snake_case filenames:
- `outputs/events_timeline.png`
- `outputs/log_level_distribution.png`
- `outputs/error_rate_hourly.png`
- `outputs/top_sources.png`

## Response Structure

After creating a visualization:

1. State the query used to extract the data.
2. Present a brief data summary (key numbers).
3. State the chart file path.
4. Add an insight about what the visualization reveals (1-2 sentences).
