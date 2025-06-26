"""
Tools exposed by the Dagster Diagnostic Agent.
"""

from .dagster_client import client

# ---------------------------------------------------------------------------
# Optional dependency: ``openai-agents`` (function_tool decorator)
# ---------------------------------------------------------------------------

try:
    from agents import function_tool  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – offline stub

    def function_tool(**_kwargs):  # noqa: D401 – decorator passthrough
        def _decorator(fn):
            return fn

        return _decorator


# ---------------------------------------------------------------------------
# fetch_dagster_logs – simple wrapper around DagsterClient
# ---------------------------------------------------------------------------


@function_tool(
    name_override="fetch_dagster_logs",
    description_override="Given a Dagster Cloud run URL, return the raw error logs.",
)
def fetch_dagster_logs(run_url: str) -> str:  # noqa: D401 – public tool
    return client.fetch_error_logs(run_url)


# ---------------------------------------------------------------------------
# diagnose_logs – OpenAI-backed log analysis (with offline fallback)
# ---------------------------------------------------------------------------


@function_tool(
    name_override="diagnose_logs",
    description_override=(
        "Given error logs, return a human-readable diagnosis and next-step recommendations."
    ),
)
def diagnose_logs(log_text: str) -> str:  # noqa: D401 – public tool
    """Analyse Dagster log excerpts and suggest next actions.

    The implementation mirrors the previous version but lives under the new
    package name.  Crucially: **never raise** – always return a string so the
    agent framework does not prepend an apology message.
    """

    # Import OpenAI or fall back to a stub when offline.
    try:
        import openai  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover – offline stub
        import types

        class _StubChoice:
            def __init__(self, content: str):
                self.message = types.SimpleNamespace(content=content)

        class _StubChatCompletion:
            @staticmethod
            def create(*_args, **_kwargs):
                # Simulate API failure in offline environment to trigger fallback logic
                raise RuntimeError("OpenAI API not available in offline environment")

        openai = types.ModuleType("openai")  # type: ignore
        openai.ChatCompletion = _StubChatCompletion  # type: ignore

    from .config import OPENAI_API_KEY

    openai.api_key = OPENAI_API_KEY

    system_prompt = (
        "You are a seasoned Dagster engineer. "
        "Diagnose the following error logs and suggest next-steps."
    )
    user_prompt = f"```\n{log_text}\n```"

    MAX_CHARS = 15_000  # guardrail
    if len(user_prompt) > MAX_CHARS:
        user_prompt = user_prompt[-MAX_CHARS:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        return response.choices[0].message.content

    except Exception as exc:  # noqa: BLE001  – broad for robustness
        lowered = log_text.lower()
        if "duplicate row" in lowered:
            hint = (
                "The logs indicate a `Duplicate row detected` database error "
                "during the snapshot step. Ensure primary keys are unique or "
                "deduplicate the upstream query."
            )
        else:
            hint = (
                "An unexpected error occurred during automatic analysis. "
                "Review the latest ERROR entries in Dagster Cloud for more details."
            )

        return (
            f"Automatic OpenAI diagnosis failed ({exc.__class__.__name__}: {exc}).\n"
            f"{hint}"
        )
