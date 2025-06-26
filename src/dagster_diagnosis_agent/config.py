"""
Configuration for Dagster Diagnosis Agent.
"""
import os

# ---------------------------------------------------------------------------
# ``python-dotenv`` is an optional dependency used to load environment
# variables from a local ``.env`` file.  The library may not be available in
# the execution environment (for example when the project is being executed in
# an isolated CI runner).  Fallback to a no-op when the import fails so that
# the module remains importable.
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except ModuleNotFoundError:  # pragma: no cover – optional dependency missing
    def load_dotenv(*_args, **_kwargs):  # noqa: D401 – no-op fallback
        return False

# Load environment variables from a .env file if present
load_dotenv()

# Dagster Cloud settings
DAGSTER_CLOUD_API_TOKEN = os.environ.get("DAGSTER_CLOUD_API_TOKEN")
# A default GraphQL endpoint path is provided for situations where the
# full URL (including any required query parameters) must be set
# explicitly via the environment.  The specific hostname and organisation /
# deployment prefix are computed from the incoming run URL at runtime, so
# only the path *and* optional query string from the environment variable
# are used.  The default path is just "/graphql", which is the standard
# location for Dagster Cloud's GraphQL API within a deployment.

DAGSTER_CLOUD_GRAPHQL_URL = os.environ.get(
    "DAGSTER_CLOUD_GRAPHQL_URL", "/graphql"
)

# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# Optional runtime environment validation
# ---------------------------------------------------------------------------

# In production these secrets *must* be configured.  During CI / local test
# runs however we purposefully avoid making real network requests.  Treat the
# settings as *optional* in those environments: if they are missing we fall
# back to obvious dummy placeholders so that importing this module never
# raises at *import-time* (which would break any form of static analysis /
# unit tests).

# The agent's runtime code – where real external calls are made – still checks
# that the secrets are present and will raise a clear error when they are not.

DAGSTER_CLOUD_API_TOKEN = DAGSTER_CLOUD_API_TOKEN or "DUMMY_DAGSTER_CLOUD_TOKEN"
OPENAI_API_KEY = OPENAI_API_KEY or "DUMMY_OPENAI_API_KEY"
