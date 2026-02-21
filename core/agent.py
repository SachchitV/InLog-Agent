"""Claude Agent SDK query logic for log analysis."""

import time
import logging

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from core.config import ANTHROPIC_API_KEY, AGENT_PROMPT, PROJECT_DIR, SCHEMAS_DIR

log = logging.getLogger("inlog-agent")


def build_prompt(file_id: str, question: str) -> str:
    """Build the agent prompt with file context and workflow state."""

    schema_path = SCHEMAS_DIR / f"{file_id}.json"

    if schema_path.exists():
        schema_content = schema_path.read_text()
        return (
            f"The user is working with log file at data/uploads/{file_id}.log. "
            f"The schema file path is data/schemas/{file_id}.json. "
            f"A schema has ALREADY been inferred and proposed to the user. "
            f"Here is the current schema:\n{schema_content}\n\n"
            f"The user's message is: {question}\n\n"
            f"If the user is confirming the schema (e.g. 'good to go', 'looks good', 'confirm', 'yes', 'parse it'), "
            f"proceed to parse the full log file using the schema above, store results in SQLite, and generate overview charts. "
            f"Do NOT re-infer the schema."
        )

    return (
        f"The user is working with log file at data/uploads/{file_id}.log. "
        f"The schema file path is data/schemas/{file_id}.json. "
        f"{question}"
    )


async def run_agent(file_id: str, question: str) -> dict:
    """Run the Claude agent and return the result as a dict matching AskResponse."""

    prompt = build_prompt(file_id, question)
    log.info(">>> Question (file_id=%s): %s", file_id, question[:120])

    start = time.time()

    options = ClaudeAgentOptions(
        system_prompt=AGENT_PROMPT,
        allowed_tools=["Bash", "Read", "Write", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        cwd=str(PROJECT_DIR),
        max_turns=10,
        env={"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY},
    )

    result_text = ""
    files: list[str] = []
    cost_usd = None
    num_turns = None
    message_count = 0

    log.info("Starting Claude Agent SDK query...")

    async for message in query(prompt=prompt, options=options):
        message_count += 1
        elapsed = time.time() - start

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
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
        "answer": result_text,
        "files": files,
        "cost_usd": cost_usd,
        "num_turns": num_turns,
    }
