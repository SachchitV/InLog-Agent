# Refining Interaction — Vision Document

## The Problem with Three Screens

Current flow forces the user through three separate screens:
1. Upload screen
2. Schema review screen
3. Charts screen

Each screen is a hard context switch. The user loses the thread of what the agent
is doing. Progress is invisible until a screen transition fires. Confirmation feels
like a bureaucratic form.

---

## The Vision: Chat + Canvas

One window. Two panes. Always.

```
── ON LOAD ────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │                      │  │                          │ │
│  │  ┌────────────────┐  │  │  Agent: Hello! Drop a    │ │
│  │  │  Drop log file │  │  │  log file on the canvas  │ │
│  │  │  or click to   │  │  │  or paste it here to     │ │
│  │  │    browse      │  │  │  get started.            │ │
│  │  └────────────────┘  │  │                          │ │
│  │                      │  │  [ chat input _________ ]│ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

── AFTER UPLOAD (schema phase) ────────────────────────────
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │                      │  │  Agent: Hello! Drop a    │ │
│  │  [Schema card]       │  │  log file...             │ │
│  │   timestamp  datetime│  │                          │ │
│  │   host       string  │  │  ┌──────────────────┐    │ │
│  │   process    string  │  │  │ 📄 syslog.log    │    │ │
│  │   pid        int     │  │  └──────────────────┘    │ │
│  │   level      enum    │  │                          │ │
│  │   message    string  │  │  Agent: Found 6 fields.  │ │
│  │                      │  │  Approve or adjust?      │ │
│  │  (no charts yet —    │  │                          │ │
│  │   awaiting approval) │  │  > Looks good, proceed   │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

── AFTER APPROVAL (charts appear) ─────────────────────────
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────────┐ │
│  │  [Schema card ✓]     │  │  ...                     │ │
│  │   6 columns, 50k rows│  │  > Looks good, proceed   │ │
│  │                      │  │                          │ │
│  │  [Chart: timeline]   │  │  Agent: Parsed 50k rows. │ │
│  │  [Chart: error dist] │  │  Two error spikes found. │ │
│  │                      │  │                          │ │
│  └──────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**The canvas is a surface the agent writes to.** The chat is how the user talks
to the agent. The agent decides what appears on the canvas and when.

This is the same mental model as Lovable, v0, Cursor — but the canvas shows
*data artifacts* (schema, charts, tables) rather than code or UI previews.

---

## Core Principles

1. **Agent drives the canvas.** The frontend renders what the agent emits.
   The agent doesn't ask the frontend for permission to show things.

2. **Agent speaks first.** When the session opens, the agent greets with a prompt
   to upload a file. The canvas shows a drop zone. The user is never on a blank screen
   wondering what to do.

3. **Chat is always open.** Upload can happen on canvas (drop zone) or inline in
   chat (paste path, drag file). Schema approval happens in chat ("looks good").
   Follow-up questions happen in chat.

4. **Uploaded files surface in chat as context chips.** After any file is uploaded,
   a persistent file list appears in the chat pane — above the input, pinned. Each
   entry is a chip: `📄 syslog.log`. Clicking a chip references it in the next
   message. The agent always knows which files are in scope.

5. **Canvas is selectable context.** Click a schema card or chart →
   it becomes `@schema` or `@chart` context in the next chat message.
   The agent sees what the user is pointing at.

6. **Progressive rendering.** Schema card appears when inferred.
   Chart appears when generated. No waiting for all three to finish.
   The canvas fills in real time as the agent works.

7. **Minimal code.** The server is a dumb pipe + event broadcaster.
   The agent decides content. Skills decide structure.

---

## Interaction Flow (target)

```
── SESSION OPENS ─────────────────────────────────────────
Canvas: [drop zone centered, dashed border]
Agent:  Hello! Drop a log file on the canvas or paste a path
        to get started.

── USER UPLOADS ──────────────────────────────────────────
User:   [drags syslog.log onto canvas drop zone]
Canvas: drop zone replaced by schema card (greyed, spinner)
Chat:   ┌────────────────────────┐  ← pinned file list appears
        │ 📄 syslog.log          │
        └────────────────────────┘
Agent:  Got it — reading syslog.log now.

── AGENT INFERS SCHEMA ───────────────────────────────────
Agent:  Found 6 fields: timestamp, host, process, pid, level, message.
Canvas: schema card fills in with column names and types
Agent:  WAITING — approve this schema or ask me to adjust.
        (canvas shows schema only — no charts yet)

── USER REVIEWS SCHEMA ───────────────────────────────────
User:   [clicks schema card on canvas → chip anchors to input]
        @schema:syslog  Can you add "service_name" from process field?
Agent:  Updated schema.
Canvas: schema card refreshes with new column
Agent:  WAITING — approve updated schema?

User:   Looks good, proceed.

── AGENT PARSES + VISUALIZES (after approval) ────────────
Agent:  Schema approved. Parsing 50,243 lines...
Canvas: row count badge appears on schema card: "50,243 rows"
Agent:  Done. Generating charts...
Canvas: timeline chart fades in below schema card
Agent:  Two error spikes at 14:32 and 22:07.
Canvas: error distribution chart fades in below

── USER EXPLORES ─────────────────────────────────────────
User:   [clicks the 14:32 spike on the timeline chart]
        @chart:timeline  What caused this spike?
Agent:  At 14:32: 47 errors from process nginx, all "upstream timeout".
Canvas: new focused chart appears — nginx errors, window 14:00–15:00
```

---

## Architecture: Agent → Canvas Protocol

The canvas is driven by structured events from the agent response stream.
The agent embeds render directives in its output — the frontend intercepts
and routes them.

### Event Types

```json
{ "type": "schema",  "data": { "table": "...", "columns": [...] } }
{ "type": "chart",   "data": { "id": "...", "title": "...", "src": "/outputs/..." } }
{ "type": "status",  "data": { "message": "Parsing 50k rows...", "step": 3 } }
{ "type": "text",    "data": { "content": "Two error spikes found." } }
{ "type": "files",   "data": { "files": [{ "id": "...", "name": "syslog.log" }] } }
```

`files` events are emitted by the server immediately after any upload completes —
not by the agent. The chat pane renders them as a persistent chip bar above the
input, always visible regardless of scroll position.

The agent emits these via Server-Sent Events (SSE) from the `/ask` endpoint.
`text` events go to the chat pane. All others go to the canvas.

**Server does not decide what to render.** It relays events. Only the agent
(through skills) knows what artifacts make sense to show.

### Canvas Selection → Chat Context

Each canvas artifact has an `id`. When a user clicks it:
- Frontend appends `@schema:syslog-2024` or `@chart:timeline` to the chat input
- Server includes the artifact's metadata in the next `/ask` request context
- Agent reads it: "User is asking about @chart:timeline — query that data"

This is the Cursor Ctrl+K model applied to data artifacts.

---

## Phases — One Step at a Time

### Phase 1: Split-Pane Layout (replace 3-screen flow)
**Goal:** Chat always open. Canvas always visible. Agent speaks first.

- [ ] Collapse `App.jsx` three-screen flow into single split-pane layout
- [ ] Left: canvas pane — on load shows centered drop zone with dashed border
- [ ] Right: chat pane — on load shows agent greeting: "Drop a log file to get started"
- [ ] Upload happens on canvas drop zone (single file per session for now)
- [ ] After upload: drop zone disappears, canvas becomes the artifact surface
- [ ] After upload: pinned file chip appears above chat input (one file)
- [ ] Schema card component: renders columns + types in a clean card
- [ ] Schema card appears in canvas when agent infers it (before approval)
- [ ] Charts appear in canvas ONLY after user approves schema in chat
- [ ] No change to backend or agent — purely frontend restructure

**Deliverable:** Same functionality, far better first-time experience. ~2 days.

---

### Phase 2: Streaming Canvas Updates (SSE)
**Goal:** Canvas fills progressively. No waiting for agent to fully complete.

- [ ] Convert `/ask` endpoint to SSE stream
- [ ] Agent response parser: split stream into `text` vs. structured events
- [ ] Canvas pane subscribes to SSE and renders events as they arrive
- [ ] Schema card renders as soon as schema event received (before parse completes)
- [ ] Status line in canvas: "Parsing row 12,000 of 50,000..."
- [ ] Charts fade in individually as each PNG is saved to `outputs/`

**Deliverable:** Real-time canvas. Agent feels alive. ~3 days.

---

### Phase 3: Canvas as Context (click-to-anchor)
**Goal:** Clicking a canvas artifact brings it into chat context.

- [ ] Each canvas artifact gets a stable `id` (e.g. `schema:syslog-2024`)
- [ ] Click handler appends `@artifact-id` token to chat input
- [ ] `/ask` request includes artifact metadata for referenced IDs
- [ ] Agent reads context: "User referenced @chart:timeline. Query store.db for that window."
- [ ] Visual: clicked artifact gets a highlight ring, token appears in chat input

**Deliverable:** Users can point at data while asking questions. ~2 days.

---

### Phase 4: Per-Artifact Chat Threads (Ctrl+K style)
**Goal:** Right-click a canvas artifact → opens focused chat thread for that artifact.

- [ ] Context menu on canvas artifacts: "Explore this", "Ask a question"
- [ ] Opens a focused chat panel with artifact pre-pinned as context
- [ ] Agent responds in narrowed scope: only the selected schema/chart's data
- [ ] Thread can be expanded back to full session
- [ ] Useful for: "Zoom into this spike", "Explain this column", "Replot as bar chart"

**Deliverable:** Cursor-like per-artifact interrogation. ~3 days.

---

### Phase 5: Multiple Files, Cross-File Queries (future)
**Goal:** Upload multiple logs at session start. Canvas shows all. Chat spans all.

- [ ] Upload screen accepts multiple files before session begins
- [ ] Agent infers schema for each file, user approves each
- [ ] Canvas shows one schema card per file, charts interleaved by time
- [ ] Agent skill `log-analysis` handles multi-table schema inference
- [ ] Chat can reference `@file:nginx-access @file:syslog` together
- [ ] Agent correlates events across files by timestamp
- [ ] Adding files mid-session is not supported — start a new session instead

**Deliverable:** Cross-log analysis. "What was nginx doing when syslog spiked?" ~1 week.

---

## What Stays Minimal Code

| Component | Lines of Code | What It Does |
|---|---|---|
| `server.py` | ~60 | HTTP transport, SSE stream relay, file save |
| `frontend/` | ~300 | Render events, layout, click handlers |
| `code/skills/lib/` | ~100 | Session paths, DB helpers |
| **Total** | **~460** | **Infrastructure only** |

All domain knowledge (schema inference rules, chart selection logic, anomaly
heuristics, narrative summaries) lives in `SKILL.md` and `agent/CLAUDE.md`.

A new log format = edit one Markdown file.
A new chart type = edit one Markdown file.
A new anomaly pattern = edit one Markdown file.

---

## Agent Awareness of Layout

The agent needs to know it has a canvas. Add to `agent/CLAUDE.md`:

```markdown
## Output Modes

You have two output channels:
- **Chat** (text): Narrative, questions, status updates, approvals
- **Canvas** (structured): Schema cards, charts, tables, status indicators

To emit a schema to canvas, include in your response:
  CANVAS:SCHEMA { ...schema json... }

To reference a chart already in outputs/:
  CANVAS:CHART { "id": "timeline", "src": "/outputs/timeline.png", "title": "..." }

The frontend routes these automatically. Users see chat text in the chat pane
and canvas events rendered as interactive cards on the left.
```

The agent learns the canvas protocol from its own CLAUDE.md — not from code.

---

## North Star Check

Ask yourself: if you wanted to add "the agent auto-detects log encoding and
converts UTF-16 to UTF-8 before parsing" — where does that go?

**Answer:** One paragraph in `log-analysis/SKILL.md` under a "Pre-processing" section.

No Python. No code review. No deployment. Edit Markdown, test, done.

That is the north star.
