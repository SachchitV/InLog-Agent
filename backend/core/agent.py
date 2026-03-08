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

# Load agent system prompt from CLAUDE.md
AGENT_PROMPT = (AGENT_DIR / "CLAUDE.md").read_text()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    log.warning("ANTHROPIC_API_KEY is not set — agent calls will fail.")

# Patterns blocked in bash commands
BLOCKED_BASH = re.compile(
    r"^\s*(rm|git|sudo|curl|wget|chmod|chown|kill)\b",
    re.IGNORECASE,
)


def _get_tool_input(input_data):
    """Extract tool_input from hook input, handling both snake_case and camelCase."""

    if not isinstance(input_data, dict):
        return {}

    return input_data.get("tool_input") or input_data.get("toolInput") or {}


def _make_access_hook(session_id: str):
    """Create a PreToolUse hook that restricts Write/Edit to session-scoped paths.

    Allowed write targets (relative to agent/ cwd):
    - workspace/{sid}/**
    - ../data/{sid}/**
    - ../outputs/{sid}/**
    Everything else is denied.
    """

    paths = get_session_paths(session_id)

    # Resolve to absolute paths for reliable comparison
    allowed_prefixes = [
        str(paths["workspace"]),
        str(paths["uploads_dir"].parent),  # data/{sid}/
        str(paths["outputs_dir"]),         # outputs/{sid}/
    ]

    async def hook(input_data, tool_use_id, context):
        try:
            tool_input = _get_tool_input(input_data)
            file_path = tool_input.get("file_path") or tool_input.get("filePath", "")

            # No file path means non-file tool (e.g. TodoWrite) — allow
            if not file_path:
                return {}

            # Resolve relative paths against agent cwd
            target = Path(file_path)
            if not target.is_absolute():
                target = AGENT_DIR / file_path
            resolved = str(target.resolve())

            for prefix in allowed_prefixes:
                if resolved.startswith(prefix):
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

        except Exception as exc:
            log.error("Access hook error (allowing): %s | input=%s", exc, input_data)
            return {}

    return hook


async def _bash_guard(input_data, tool_use_id, context):
    """Block dangerous bash commands."""

    try:
        tool_input = _get_tool_input(input_data)
        command = tool_input.get("command", "")

        if BLOCKED_BASH.search(command):
            log.warning("Bash blocked: %s", command[:80])
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked dangerous command: {command[:80]}",
                }
            }

        return {}

    except Exception as exc:
        log.error("Bash guard error (allowing): %s | input=%s", exc, input_data)
        return {}


def build_prompt(session_id: str, file_id: str, question: str) -> str:
    """Build the agent prompt with session-scoped file context."""

    paths = get_session_paths(session_id)
    schema_path = paths["schemas_dir"] / f"{file_id}.json"

    # Paths relative to agent/ cwd (what the agent sees)
    uploads_rel = f"../data/{session_id}/uploads/{file_id}.log"
    schemas_rel = f"../data/{session_id}/schemas/{file_id}.json"

    if schema_path.exists():
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

    return (
        f"Session: {session_id}. "
        f"The user is working with log file at {uploads_rel}. "
        f"The schema file path is {schemas_rel}. "
        f"{question}"
    )


async def run_agent(session_id: str, file_id: str, question: str) -> dict:
    """Run the Claude agent with session-scoped hooks and return the result."""

    prompt = build_prompt(session_id, file_id, question)
    log.info(">>> Question (sid=%s, file=%s): %s", session_id, file_id, question[:120])

    start = time.time()

    # Log CLI stderr for hook diagnostics
    def _on_stderr(line: str):
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
        cwd=str(AGENT_DIR),
        max_turns=20,
        stderr=_on_stderr,
        env={"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY},
    )

    result_text = ""
    last_assistant_text = ""
    files: list[str] = []
    cost_usd = None
    num_turns = None
    message_count = 0

    log.info("Starting Claude Agent SDK query...")

    async for message in query(prompt=prompt, options=options):
        message_count += 1
        elapsed = time.time() - start

        if isinstance(message, AssistantMessage):
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
                    # Track files written to outputs/
                    if block.name == "Write":
                        file_path = block.input.get("file_path", "")
                        if "outputs/" in file_path:
                            files.append(file_path)

                elif isinstance(block, ToolResultBlock):
                    preview = str(block.content)[:120] if block.content else "(empty)"
                    log.info("[%.1fs] Tool result: %s", elapsed, preview)

            # Keep last assistant text as fallback
            if turn_text_parts:
                last_assistant_text = "\n\n".join(turn_text_parts)

        elif isinstance(message, ResultMessage):
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
        "answer": result_text or last_assistant_text,
        "files": files,
        "cost_usd": cost_usd,
        "num_turns": num_turns,
    }