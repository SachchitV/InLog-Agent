"""Claude Agent SDK query logic for log analysis.

Wraps the SDK to spawn the agent with session-scoped access control
via PreToolUse hooks instead of static permission rules.
"""

import logging
import os
import re
import time
from pathlib import Path

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from core.config import PROJECT_DIR
from core.session import AGENT_DIR, get_session_paths

log = logging.getLogger(__name__)

AGENT_PROMPT = (AGENT_DIR / "CLAUDE.md").read_text()  # agent identity + workflow rules

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    log.warning("ANTHROPIC_API_KEY is not set — agent calls will fail.")

# Commands the agent must never run (destructive or network ops)
BLOCKED_BASH = re.compile(
    r"^\s*(rm|git|sudo|curl|wget|chmod|chown|kill)\b",
    re.IGNORECASE,
)


def _get_tool_input(input_data):
    """Extract the tool input dict from a hook payload.

    The SDK may deliver the payload with either snake_case (``tool_input``) or
    camelCase (``toolInput``) depending on the version, so both are checked.

    Args:
        input_data: Raw hook input, expected to be a dict.

    Returns:
        dict: The tool input dict, or an empty dict if not found or if
            ``input_data`` is not a dict.
    """
    if not isinstance(input_data, dict):
        return {}

    return input_data.get("tool_input") or input_data.get("toolInput") or {}


def _make_access_hook(session_id: str):
    """Create a PreToolUse hook that restricts Write/Edit to session-scoped paths.

    Allowed write targets (resolved to absolute paths):
    - ``agent/workspace/{sid}/``
    - ``backend/data/{sid}/``
    - ``backend/outputs/{sid}/``

    Any Write or Edit attempt outside these prefixes is denied with a
    ``permissionDecision: deny`` response, protecting other sessions and
    read-only areas like ``.claude/skills/``.

    Args:
        session_id: The active session ID used to derive the allowed path prefixes.

    Returns:
        Callable: An async hook function compatible with the SDK's PreToolUse
            hook interface.
    """

    paths = get_session_paths(session_id)

    allowed_prefixes = [
        str(paths["workspace"]),           # agent scripts + working files
        str(paths["uploads_dir"].parent),  # data/{sid}/ — schemas + db
        str(paths["outputs_dir"]),         # chart PNGs served by FastAPI
    ]

    async def hook(input_data, tool_use_id, context):
        """Evaluate a single Write/Edit tool call against allowed path prefixes.

        Args:
            input_data: Hook payload dict from the SDK.
            tool_use_id: Unique ID for this tool use (unused, required by SDK).
            context: SDK-provided context object (unused).

        Returns:
            dict: Empty dict to allow the tool call, or a deny decision dict.
        """
        try:
            tool_input = _get_tool_input(input_data)
            file_path = tool_input.get("file_path") or tool_input.get("filePath", "")

            if not file_path:  # non-file tools (e.g. TodoWrite) — always allow
                return {}

            # Relative paths are anchored to agent/ cwd, not the process cwd
            target = Path(file_path)
            if not target.is_absolute():
                target = AGENT_DIR / file_path
            resolved = str(target.resolve())

            if any(resolved.startswith(p) for p in allowed_prefixes):  # path is in scope
                return {}

            log.warning("Write blocked: %s (outside session %s)", file_path, session_id)
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Write blocked: {file_path} is outside session scope."
                    ),
                }
            }

        except Exception as exc:  # hook errors must never crash the agent turn
            log.error("Access hook error (allowing): %s | input=%s", exc, input_data)
            return {}

    return hook


async def _bash_guard(input_data, tool_use_id, context):
    """PreToolUse hook that blocks dangerous shell commands.

    Denies any Bash call whose command matches the ``BLOCKED_BASH`` pattern
    (``rm``, ``git``, ``sudo``, ``curl``, ``wget``, ``chmod``, ``chown``,
    ``kill``). Errors in the hook itself are logged and treated as allow to
    avoid silently breaking the agent.

    Args:
        input_data: Hook payload dict from the SDK.
        tool_use_id: Unique ID for this tool use (unused, required by SDK).
        context: SDK-provided context object (unused).

    Returns:
        dict: Empty dict to allow, or a deny decision dict.
    """

    try:
        tool_input = _get_tool_input(input_data)
        command = tool_input.get("command", "")

        if BLOCKED_BASH.search(command):  # matches dangerous command prefix
            log.warning("Bash blocked: %s", command[:80])
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked dangerous command: {command[:80]}",
                }
            }

        return {}

    except Exception as exc:  # hook errors must never crash the agent turn
        log.error("Bash guard error (allowing): %s | input=%s", exc, input_data)
        return {}


def build_prompt(session_id: str, file_id: str, question: str) -> str:
    """Build the prompt string passed to the Claude agent.

    Injects session-scoped file paths and the user's question. When a schema
    file already exists for this file, its contents are embedded so the agent
    does not re-infer the schema; it is instead directed to confirm and proceed
    with parsing.

    Args:
        session_id: Active session ID used to resolve data paths.
        file_id: ID of the uploaded log file to analyse.
        question: Raw question or instruction from the user.

    Returns:
        str: A fully-formed prompt string ready to pass to ``query()``.
    """

    paths = get_session_paths(session_id)
    schema_path = paths["schemas_dir"] / f"{file_id}.json"

    # Paths expressed relative to agent/ so they match the agent's cwd
    uploads_rel = f"../data/{session_id}/uploads/{file_id}.log"
    schemas_rel = f"../data/{session_id}/schemas/{file_id}.json"

    if schema_path.exists():  # schema already inferred — skip straight to parse/chart
        schema_content = schema_path.read_text()
        return (
            f"Session: {session_id}. "
            f"The user is working with log file at {uploads_rel}. "
            f"The schema file path is {schemas_rel}. "
            f"A schema has ALREADY been inferred and proposed to the user. "
            f"Here is the current schema:\n{schema_content}\n\n"
            f"The user's message is: {question}\n\n"
            f"If the user is confirming the schema (e.g. 'good to go', 'looks good', "
            f"'confirm', 'yes', 'parse it'), proceed to parse the full log file "
            f"using the schema above, store results in SQLite, and generate "
            f"overview charts. Do NOT re-infer the schema."
        )

    # No schema yet — agent should read the log and infer one
    return (
        f"Session: {session_id}. "
        f"The user is working with log file at {uploads_rel}. "
        f"The schema file path is {schemas_rel}. "
        f"{question}"
    )


async def run_agent(session_id: str, file_id: str, question: str) -> dict:
    """Run the Claude agent for one user turn and stream the result.

    Spawns a Claude Code CLI subprocess via the Agent SDK, configured with:
    - A system prompt loaded from ``agent/CLAUDE.md``
    - A PreToolUse access hook restricting writes to session-scoped paths
    - A PreToolUse bash guard blocking dangerous shell commands
    - A max of 20 agentic turns per call

    Captures text responses, chart file paths written to ``outputs/``, and
    todo-list snapshots from ``TodoWrite`` calls for observability.

    Args:
        session_id: Active session ID; used to scope file access and build
            the prompt.
        file_id: ID of the log file the agent should operate on.
        question: User's message or instruction for this turn.

    Returns:
        dict with keys:
            - ``answer`` (str): Final agent response text.
            - ``files`` (list[str]): Paths of chart PNGs written this turn.
            - ``todos`` (list[dict]): Latest todo snapshot from ``TodoWrite``.
            - ``cost_usd`` (float | None): Anthropic API cost for this turn.
            - ``num_turns`` (int | None): Number of agentic turns taken.

    Raises:
        Exception: Any unhandled SDK or subprocess error propagates to the caller.
    """

    prompt = build_prompt(session_id, file_id, question)
    log.info(">>> Question (sid=%s, file=%s): %s", session_id, file_id, question[:120])

    start = time.time()

    def _on_stderr(line: str):  # surface CLI subprocess stderr in our logs
        log.debug("CLI: %s", line.rstrip())

    options = ClaudeAgentOptions(
        system_prompt=AGENT_PROMPT,
        allowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep", "TodoRead", "TodoWrite"],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Write|Edit", hooks=[_make_access_hook(session_id)]),
                HookMatcher(matcher="Bash", hooks=[_bash_guard]),
            ],
        },
        cwd=str(AGENT_DIR),   # agent/ is the working root; all relative paths resolve here
        max_turns=20,
        stderr=_on_stderr,
        env={"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY},
    )

    result_text = ""        # populated by ResultMessage (SDK's final summary)
    last_assistant_text = ""  # fallback if ResultMessage.result is empty
    files: list[str] = []  # chart PNGs detected via Write tool calls
    todos: list[dict] = []  # latest TodoWrite snapshot — reflects agent's current plan
    cost_usd = None
    num_turns = None
    message_count = 0

    log.info("Starting Claude Agent SDK query...")

    async for message in query(prompt=prompt, options=options):
        message_count += 1
        elapsed = time.time() - start

        if isinstance(message, AssistantMessage):  # one assistant turn (may contain multiple blocks)
            turn_text_parts = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    turn_text_parts.append(block.text)
                    preview = block.text[:120].replace("\n", " ")
                    log.info(
                        "[%.1fs] Assistant text: %s%s",
                        elapsed, preview,
                        "..." if len(block.text) > 120 else "",
                    )

                elif isinstance(block, ToolUseBlock):
                    log.info(
                        "[%.1fs] Tool call: %s(%s)",
                        elapsed, block.name, str(block.input)[:100],
                    )
                    if block.name == "Write":  # track chart files written to outputs/
                        file_path = block.input.get("file_path", "")
                        if "outputs/" in file_path:
                            files.append(file_path)
                    elif block.name == "TodoWrite":  # replace stale todos with latest snapshot
                        snapshot = block.input.get("todos", [])
                        todos.clear()
                        todos.extend(snapshot)
                        log.info("[%.1fs] Todos: %s", elapsed, snapshot)

                elif isinstance(block, ToolResultBlock):
                    preview = str(block.content)[:120] if block.content else "(empty)"
                    log.info("[%.1fs] Tool result: %s", elapsed, preview)

            if turn_text_parts:  # accumulate text; last turn wins as fallback answer
                last_assistant_text = "\n\n".join(turn_text_parts)

        elif isinstance(message, ResultMessage):  # terminal message — extract cost + answer
            result_text = message.result or ""
            cost_usd = message.total_cost_usd
            num_turns = message.num_turns
            log.info(
                "[%.1fs] Result: turns=%s, cost=$%s, error=%s",
                elapsed, message.num_turns, message.total_cost_usd, message.is_error,
            )

        elif isinstance(message, SystemMessage):
            log.info("[%.1fs] System message: subtype=%s", elapsed, message.subtype)

        else:
            log.info("[%.1fs] Other message: %s", elapsed, type(message).__name__)

    elapsed = time.time() - start
    log.info(
        "<<< Done in %.1fs (%d messages). Answer length: %d chars",
        elapsed, message_count, len(result_text),
    )

    return {
        "answer": result_text or last_assistant_text,  # prefer SDK summary, fall back to last text block
        "files": files,
        "todos": todos,
        "cost_usd": cost_usd,
        "num_turns": num_turns,
    }
