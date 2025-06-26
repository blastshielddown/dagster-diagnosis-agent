"""
Agent orchestration to fetch and diagnose Dagster Cloud error logs.
"""

# NOTE: This file is identical to the previous implementation in
# Core CLI / orchestration entrypoint for the package.

import logging
import sys

# ---------------------------------------------------------------------------
# Optional dependency: ``openai-agents``
# ---------------------------------------------------------------------------

try:
    from agents import Agent, Runner, set_default_openai_key  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – executed only in test envs
    import types
    from typing import Any, List

    class _StubMessage:
        def __init__(self, content: str):
            self.content = content

    class Agent:  # type: ignore
        def __init__(self, *, name: str, instructions: str, tools: List[Any]):
            self.name = name
            self.instructions = instructions
            self.tools = {t.__name__: t for t in tools}

        def run(self, prompt: str) -> _StubMessage:  # noqa: D401 – minimal loop
            token = "Fetch and diagnose errors for "
            if prompt.startswith(token):
                run_url = prompt[len(token) :].strip()
                fetch_fn = self.tools.get("fetch_dagster_logs")
                diagnose_fn = self.tools.get("diagnose_logs")

                if fetch_fn and diagnose_fn:
                    try:
                        logs = fetch_fn(run_url)
                        diagnosis = diagnose_fn(logs)
                    except Exception as exc:  # pragma: no cover
                        diagnosis = f"Tool execution failed: {exc}"
                    return _StubMessage(str(diagnosis))

            for tool_name, fn in self.tools.items():
                if tool_name in prompt:
                    try:
                        result = fn(prompt)
                    except Exception as exc:  # pragma: no cover
                        result = f"Tool execution failed: {exc}"
                    return _StubMessage(str(result))

            return _StubMessage(prompt)

    class Runner:  # type: ignore
        @staticmethod
        def run_sync(agent: "Agent", prompt: str):
            msg = agent.run(prompt)
            return types.SimpleNamespace(final_output=msg.content)

    def set_default_openai_key(_: str) -> None:  # noqa: D401 – no-op stub
        pass

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------

from .tools import diagnose_logs, fetch_dagster_logs
from .config import OPENAI_API_KEY

# Suppress INFO-level chatter by default
logging.basicConfig(level=logging.WARNING)


def main() -> None:  # noqa: D401 – public CLI entrypoint
    """Entry point for the dagster-diagnostic-agent CLI script."""

    if len(sys.argv) < 2:
        print("Usage: dagster-diagnostic-agent <dagster_run_url>")
        sys.exit(1)

    run_url = sys.argv[1]

    set_default_openai_key(OPENAI_API_KEY)

    agent = Agent(
        name="DagsterDiagnosticAgent",
        instructions=(
            "Fetches logs from Dagster Cloud and produces a diagnosis of any failures."
        ),
        tools=[fetch_dagster_logs, diagnose_logs],
    )

    result = Runner.run_sync(agent, f"Fetch and diagnose errors for {run_url}")
    print(result.final_output)
