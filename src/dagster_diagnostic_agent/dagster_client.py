"""
Client for interacting with Dagster Cloud GraphQL API.

This is a direct copy of the original implementation under
``dagster_diagnosis_agent``.  Only the import path for the sibling *config*
module changes to reflect the new package name.
"""

import logging
import re
from typing import List
from urllib.parse import urlparse

# Optional dependency: ``dagster-graphql``
try:
    from dagster_graphql.client import DagsterGraphQLClient  # type: ignore
    from dagster_graphql.client.query import RUN_EVENTS_QUERY  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – offline / CI stub

    class _StubDagsterGraphQLClient:  # noqa: D401 – minimal placeholder
        def __init__(self, *_, **__):
            pass

        def _execute(self, *_args, **_kwargs):  # noqa: D401 – always empty
            return {"logsForRun": {"events": [], "cursor": None}}

    DagsterGraphQLClient = _StubDagsterGraphQLClient  # type: ignore
    RUN_EVENTS_QUERY = "RUN_EVENTS_QUERY"


from .config import DAGSTER_CLOUD_API_TOKEN


logger = logging.getLogger(__name__)


class DagsterClient:
    """Light wrapper around DagsterGraphQLClient to fetch run error logs."""

    def __init__(self, token: str):
        self._token = token
        self._client_cache: dict[str, DagsterGraphQLClient] = {}

    # ------------------------------------------------------------ helpers ---

    def _parse_run_id(self, run_url: str) -> str:
        match = re.search(r"/runs/([^/?#]+)", run_url)
        if not match:
            raise ValueError(f"Cannot parse run ID from URL: {run_url}")
        return match.group(1)

    def _get_graphql_client(self, run_url: str) -> DagsterGraphQLClient:  # noqa: D401
        parsed = urlparse(run_url)

        try:
            prefix, _ = parsed.path.split("/runs/", 1)
        except ValueError as exc:  # pragma: no cover – invalid URL
            raise ValueError("'/runs/' not found in Dagster run URL") from exc

        prefix = prefix.rstrip("/")
        hostname = parsed.netloc + (prefix or "")

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

    # ----------------------------------------------------------- public API

    def fetch_error_logs(self, run_url: str) -> str:  # noqa: D401
        """Return ERROR-level log messages as a newline-delimited string."""

        run_id = self._parse_run_id(run_url)
        gql_client = self._get_graphql_client(run_url)

        cursor = None
        all_events: List[dict] = []

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


# Default pre-instantiated client used by tool wrappers
client = DagsterClient(token=DAGSTER_CLOUD_API_TOKEN)

