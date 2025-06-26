"""
Tools exposed to the Dagster Diagnosis Agent.
"""
from .dagster_client import client

from agents import function_tool


@function_tool(
    name_override="fetch_dagster_logs",
    description_override="Given a Dagster Cloud run URL, return the raw error logs.",
)
def fetch_dagster_logs(run_url: str) -> str:
    """
    Tool to fetch error logs from a Dagster Cloud run.
    """
    return client.fetch_error_logs(run_url)


@function_tool(
    name_override="diagnose_logs",
    description_override="Given error logs, return a natural-language diagnosis and next-step recommendations.",
)
def diagnose_logs(log_text: str) -> str:
    """
    Tool to diagnose Dagster error logs via OpenAI LLM.
    """
    import openai

    from .config import OPENAI_API_KEY

    # Configure OpenAI API key
    openai.api_key = OPENAI_API_KEY

    # System prompt for diagnosis context
    system_prompt = (
        "You are a seasoned Dagster engineer. "
        "Diagnose the following error logs and suggest next-steps."
    )
    user_prompt = f"```\n{log_text}\n```"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    # Extract and return the assistant's response
    return response.choices[0].message.content
