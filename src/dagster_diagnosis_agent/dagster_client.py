"""
Client for interacting with Dagster Cloud GraphQL API.
"""
import logging
import re
from typing import List
from urllib.parse import urlparse

# ``dagster-graphql`` is an optional dependency that is only required when the
# client actually needs to fetch logs from a live Dagster Cloud deployment.
# Unit-test environments that do not have the dependency installed can still
# import this module thanks to the lightweight shims below.

try:
    from dagster_graphql.client import DagsterGraphQLClient  # type: ignore
    from dagster_graphql.client.query import RUN_EVENTS_QUERY  # type: ignore

except ModuleNotFoundError:  # pragma: no cover – executed only in test envs
    class _StubDagsterGraphQLClient:  # noqa: D401 – minimal stub
        """Very small stand-in that mimics the handful of APIs we consume."""

        def __init__(self, *_, **__):
            pass

        # The real ``DagsterGraphQLClient`` exposes ``_execute`` – we keep the
        # same method name so that the remainder of the code remains
        # unchanged.  The stub implementation simply returns an empty
        # connection so that callers believe there are no events.
        def _execute(self, *_args, **_kwargs):  # noqa: D401 – stub method
            return {"logsForRun": {"events": [], "cursor": None}}

    DagsterGraphQLClient = _StubDagsterGraphQLClient  # type: ignore

    # The particular GraphQL query object is only used as an opaque identifier
    # when communicating with the *real* API.  For our stub we can use any
    # sentinel value.
    RUN_EVENTS_QUERY = "RUN_EVENTS_QUERY"

from .config import DAGSTER_CLOUD_API_TOKEN


logger = logging.getLogger(__name__)


class DagsterClient:
    """Light wrapper around DagsterGraphQLClient to fetch run error logs.

    Dagster maintains an official GraphQL client (``dagster-graphql``).  Using the
    official client means we no longer need to hand-roll HTTP requests or worry
    about subtle authentication / URL-building edge-cases – the library already
    handles these for us.  We still keep a very small amount of code to:

    1.  Translate a Dagster Cloud *run URL* into the host / deployment path that
        the client expects.
    2.  Extract and post-process the log messages so that callers receive a
        plain-text list of ``ERROR`` entries.
    """

    def __init__(self, token: str):
        self._token = token
        # Cache GraphQL clients per (scheme, host+path) so that multiple calls
        # to the same deployment do not continually re-instantiate the client /
        # fetch the GraphQL schema.
        self._client_cache: dict[str, DagsterGraphQLClient] = {}

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _parse_run_id(self, run_url: str) -> str:
        """Extract the Dagster run UUID from a Dagster Cloud run URL."""
        match = re.search(r"/runs/([^/?#]+)", run_url)
        if not match:
            raise ValueError(f"Cannot parse run ID from URL: {run_url}")
        return match.group(1)

    def _get_graphql_client(self, run_url: str) -> DagsterGraphQLClient:
        """Return (and cache) a DagsterGraphQLClient for the deployment in *run_url*."""

        parsed = urlparse(run_url)

        try:
            prefix, _ = parsed.path.split("/runs/", 1)
        except ValueError as exc:
            raise ValueError("'/runs/' not found in Dagster run URL") from exc

        # "prefix" is either "" (if the org / deployment is encoded in the
        # sub-domain) **or** something like "/prod" or "/my-org/prod" when the
        # deployment lives under a path prefix.
        prefix = prefix.rstrip("/")

        # DagsterGraphQLClient builds the URL as "https://{hostname}/graphql".
        # To hit e.g. "https://fleetio.dagster.cloud/prod/graphql" we therefore
        # need to treat "fleetio.dagster.cloud/prod" as the *hostname*.
        hostname = parsed.netloc + (prefix or "")

        # Use cached client if available.
        cache_key = f"{parsed.scheme}://{hostname}"
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]

        client = DagsterGraphQLClient(
            hostname=hostname,
            use_https=parsed.scheme == "https",
            headers={"Dagster-Cloud-Api-Token": self._token},
        )

        self._client_cache[cache_key] = client
        return client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_error_logs(self, run_url: str) -> str:
        """Return ``ERROR``-level log messages for *run_url* as a newline string."""

        run_id = self._parse_run_id(run_url)
        gql_client = self._get_graphql_client(run_url)

        # RUN_EVENTS_QUERY returns *all* event types.  We only care about the
        # message-level fields (level, timestamp, message) which are embedded in
        # the ``messageEventFragment`` that the Dagster library already defines.
        logger.info("Fetching logs for run_id=%s via DagsterGraphQLClient", run_id)

        cursor = None
        all_events: List[dict] = []

        # Paginate until the API indicates there are no more events by returning
        # an empty cursor.
        while True:
            variables = {"runId": run_id, "cursor": cursor}
            page = gql_client._execute(RUN_EVENTS_QUERY, variables)  # type: ignore[attr-defined]

            conn = page.get("logsForRun", {}) if isinstance(page, dict) else {}
            events = conn.get("events", []) if isinstance(conn, dict) else []
            all_events.extend(events)

            next_cursor = conn.get("cursor") if isinstance(conn, dict) else None
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor

        errors: List[str] = []
        for evt in all_events:
            if not isinstance(evt, dict):
                continue
            if evt.get("level") != "ERROR":
                continue

            ts = evt.get("timestamp", "")
            base_msg = evt.get("message", "")

            # Include nested PythonError messages when present so that callers
            # have more context than the terse surface-level message.
            nested_error_msg = None
            if isinstance(evt.get("error"), dict):
                nested_error_msg = evt["error"].get("message")

            if nested_error_msg and nested_error_msg not in base_msg:
                combined = f"{base_msg} | {nested_error_msg}"
            else:
                combined = base_msg

            errors.append(f"{ts} - {combined}".strip())

        logger.info("Total events fetched: %s, error-level: %s", len(all_events), len(errors))

        if not errors:
            return f"No error logs found for run: {run_id}"

        return "\n".join(errors)


# -------------------------------------------------------------------------
# Default instance used by the agent's tool implementations
# -------------------------------------------------------------------------


client = DagsterClient(token=DAGSTER_CLOUD_API_TOKEN)
