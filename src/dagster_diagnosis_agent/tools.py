"""
Tools exposed to the Dagster Diagnosis Agent.
"""
from .dagster_client import client

# ``function_tool`` is a thin decorator provided by the ``openai-agents``
# package.  To keep optionality symmetrical with the rest of the codebase we
# provide a no-op replacement when the dependency is missing so that the
# module can still be imported in lightweight environments.

try:
    from agents import function_tool  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – executed only in test envs

    def function_tool(**_kwargs):  # noqa: D401 – very small decorator stub
        def _decorator(fn):  # noqa: D401 – inner wrapper returns original func
            return fn

        return _decorator


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
    # ``openai`` is required to actually call the ChatCompletion API.  When
    # the library is absent (e.g. in an offline CI environment) we instead
    # fall back to a *very* small stub that returns a deterministic canned
    # response so that the rest of the code continues to run.

    try:
        import openai  # type: ignore

        openai_available = True
    except ModuleNotFoundError:  # pragma: no cover – executed only in test envs

        class _StubChoice:  # noqa: D401 – minimal stand-in for OpenAI choice
            def __init__(self, content: str):  # noqa: D401 – simple init
                self.message = types.SimpleNamespace(content=content)

        class _StubChatCompletion:  # noqa: D401 – mimic subset of OpenAI API
            @staticmethod
            def create(*_args, **_kwargs):  # noqa: D401 – stub create method
                # Return a generic but helpful response so that downstream code
                # behaves as though a real OpenAI call had succeeded.
                return types.SimpleNamespace(
                    choices=[_StubChoice("Stub diagnosis: unable to run in the"
                                         " current offline environment.")]
                )

        import types

        openai = types.ModuleType("openai")  # type: ignore
        openai.ChatCompletion = _StubChatCompletion  # type: ignore
        openai_available = False

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
