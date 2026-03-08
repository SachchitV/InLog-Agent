# Agent Cost Analysis

Cost breakdown from integration test runs (`test_agent_flow.py`) using
`rfnd_flight_telemetry.csv` (~3MB, 25k rows, single RFND message type).

## Observed Costs

| Run | Step 1 (infer) | Step 2 (parse+chart) | Total | Duration |
|-----|---------------|---------------------|-------|----------|
| 1   | $0.75 / 23 turns | — (failed)       | $0.75 | ~170s    |
| 2   | $0.46 / 17 turns | $0.43 / 18 turns | $0.89 | ~298s    |
| 3   | $0.40 / 20 turns | $0.35 / 15 turns | $0.75 | ~232s    |

## Cost Drivers (ranked by impact)

### 1. Path key trial-and-error (2-4 wasted turns per call)

Every run, the agent writes a script using wrong `get_session_paths()` keys
(e.g. `paths["uploads"]` instead of `paths["uploads_dir"]`), hits a KeyError,
introspects the function, then fixes. This happened in all 3 observed runs.

**Fix:** Add the exact dict keys to the ad-hoc scripting example in
`backend/agent/CLAUDE.md` so the agent sees them in its system prompt.
Status: **Done** (this commit).

### 2. Two CLI cold starts (~56s each, ~112s total)

Each `run_agent()` call spawns a fresh Claude Code CLI subprocess. The bundled
CLI takes ~56s to initialize before the first tool call. For a two-step flow,
that's ~2 minutes of idle wait.

**Fix:** Investigate SDK options for persistent/warm CLI processes, or combine
both steps into a single `run_agent()` call with a multi-step prompt.

### 3. Large system prompt (244 lines)

The full `agent/CLAUDE.md` is loaded as the system prompt on every call.
Much of it (resumption protocol, error handling, learning rule) is irrelevant
for simple infer-then-parse flows.

**Fix:** Consider a tiered prompt strategy — minimal prompt for common flows,
full prompt only for complex/multi-session scenarios.

### 4. Session ceremony (3-5 turns overhead)

The agent's "First Action" protocol requires checking for existing sessions,
reading state.json, and updating decisions.md — even when the server already
set up the session and passed context via `build_prompt()`.

**Fix:** Streamline the first-action protocol. The server's `build_prompt()`
already provides session context; the agent doesn't need to re-discover it.

### 5. File exploration (3-5 turns)

The agent reads the CSV in multiple chunks and runs bash analytics (wc, cut,
python one-liners) to understand the data before writing the inference script.
This is somewhat necessary but could be reduced.

**Fix:** Pre-compute basic file stats (line count, sample rows) in
`build_prompt()` so the agent doesn't need exploratory tool calls.
