"""
Configuration for Dagster Diagnostic Agent.
"""

# The file content mirrors the previous implementation (when the package was
# named ``dagster_diagnosis_agent``) so that external behaviour is preserved.

import os


# ---------------------------------------------------------------------------
# Optional dependency: ``python-dotenv``
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except ModuleNotFoundError:  # pragma: no cover – optional dependency missing

    def load_dotenv(*_args, **_kwargs):  # noqa: D401 – no-op fallback
        return False


# Load environment variables from a .env file if present
load_dotenv()


# ---------------------------------------------------------------------------
# Dagster Cloud / OpenAI configuration
# ---------------------------------------------------------------------------

DAGSTER_CLOUD_API_TOKEN = os.environ.get("DAGSTER_CLOUD_API_TOKEN")
DAGSTER_CLOUD_GRAPHQL_URL = os.environ.get("DAGSTER_CLOUD_GRAPHQL_URL", "/graphql")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Provide obvious placeholders so that importing the module never crashes in
# CI environments where the real secrets are unavailable.

DAGSTER_CLOUD_API_TOKEN = DAGSTER_CLOUD_API_TOKEN or "DUMMY_DAGSTER_CLOUD_TOKEN"
OPENAI_API_KEY = OPENAI_API_KEY or "DUMMY_OPENAI_API_KEY"

