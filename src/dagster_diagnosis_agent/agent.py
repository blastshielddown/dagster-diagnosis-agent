"""
Agent orchestration to fetch and diagnose Dagster Cloud error logs.
"""
import sys

from openai_agents import Agent, OpenAI

from .tools import fetch_dagster_logs, diagnose_logs
from .config import OPENAI_API_KEY


def main() -> None:
    """
    Entry point for the dagster-diagnosis-agent script.
    """
    # Require a run URL argument
    if len(sys.argv) < 2:
        print("Usage: dagster-diagnosis-agent <dagster_run_url>")
        sys.exit(1)

    run_url = sys.argv[1]

    # Initialize the OpenAI LLM
    llm = OpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4",
        temperature=0,
    )

    # Build the agent with our two tools
    agent = Agent.from_tools(
        tools=[fetch_dagster_logs, diagnose_logs],
        llm=llm,
        name="DagsterDiagnosisAgent",
        description=(
            "Fetches logs from Dagster Cloud and diagnoses the failures."
        ),
    )

    # Run the agent: fetch logs, then diagnose
    result = agent.run(f"Fetch and diagnose errors for {run_url}")
    print(result)
