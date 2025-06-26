"""
Client for interacting with Dagster Cloud GraphQL API.
"""
import re
from typing import List

import requests

from .config import DAGSTER_CLOUD_API_TOKEN, DAGSTER_CLOUD_GRAPHQL_URL


class DagsterClient:
    """
    A simple GraphQL client to fetch error logs for a Dagster run.
    """
    def __init__(self, token: str, graphql_url: str) -> None:
        self.token = token
        self.url = graphql_url

    def _parse_run_id(self, run_url: str) -> str:
        """
        Extract the run ID from a Dagster Cloud run URL.
        """
        # Example URL: https://dagster.cloud/org/ORG_NAME/runs/RUN_ID
        match = re.search(r"/runs/([^/?#]+)", run_url)
        if not match:
            raise ValueError(f"Cannot parse run ID from URL: {run_url}")
        return match.group(1)

    def fetch_error_logs(self, run_url: str) -> str:
        """
        Fetch and return all error-level log messages for the given run.
        """
        run_id = self._parse_run_id(run_url)
        query = """
        query PipelineRunLogs($runId: ID!) {
          pipelineRunOrError(runId: $runId) {
            __typename
            ... on PipelineRun {
              logs {
                nodes {
                  level
                  timestamp
                  message
                }
              }
            }
          }
        }
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": {"runId": run_id}}
        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        result = data.get("data", {}).get("pipelineRunOrError")
        if not result or result.get("__typename") != "PipelineRun":
            raise RuntimeError(f"Failed to fetch run logs: {result}")

        # Filter for error-level logs
        entries = result["logs"]["nodes"] or []
        errors: List[str] = []
        for node in entries:
            if node.get("level") == "ERROR":
                ts = node.get("timestamp") or ""
                msg = node.get("message", "")
                errors.append(f"{ts} - {msg}")

        if not errors:
            return "No error logs found for run: {run_id}"
        return "\n".join(errors)


# Default client for tools
client = DagsterClient(
    token=DAGSTER_CLOUD_API_TOKEN, graphql_url=DAGSTER_CLOUD_GRAPHQL_URL
)
