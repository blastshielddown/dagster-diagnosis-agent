"""Console-script entry for the Dagster Diagnostic Agent."""

# Re-export the CLI entrypoint so `python -m dagster_diagnostic_agent` and the
# console script both resolve to the same function.

from .agent import main  # noqa: F401 – re-export for convenience

