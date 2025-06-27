# dagster-diagnostic-agent

A diagnostic agent for Dagster.

## Requirements

- Python >=3.12
- uv (https://github.com/astral-sh/uv)

## Setup

Install uv and sync the project environment (including optional extras):

```bash
pip install uv
uv lock && uv sync --all-extras
```

### Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` to set:
```dotenv
DAGSTER_CLOUD_API_TOKEN=your-dagster-cloud-token
OPENAI_API_KEY=your-openai-api-key
# (Optional) DAGSTER_CLOUD_GRAPHQL_URL=https://dagster.cloud/api/graphql
```

## Running

Run the agent script with a Dagster Cloud run URL:

```bash
uv run dagster-diagnostic-agent https://<your-dagster-domain>/org/<org-name>/runs/<run-id>
```

## Triggering via GitHub Actions

You can trigger this agent through a GitHub Actions workflow defined in `.github/workflows/trigger-agent.yml`. The workflow exposes the following `workflow_dispatch` inputs:

- `run_url` (required): URL of the Dagster run to diagnose (e.g. `https://<domain>/org/<org>/runs/<run-id>`).
- `dagster_cloud_graphql_url` (optional): Override the Dagster Cloud GraphQL API endpoint.
- `callback_url` (required): HTTP endpoint to POST the agent output once the workflow completes.

### Repository Setup

1. Add the following **Secrets** in your GitHub repository (`Settings → Secrets`):
   - `DAGSTER_CLOUD_API_TOKEN`: Your Dagster Cloud API token.
   - `OPENAI_API_KEY`: Your OpenAI API key.

2. (Optional) Add a GitHub Actions **Variable** (`Settings → Variables → Actions`):
   - `RUNS_ON`: The runner environment (defaults to `ubuntu-latest`).

### Dispatching the Workflow

Use the GitHub REST API to dispatch the workflow. Example:

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GH_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/trigger-agent.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "run_url": "https://<domain>/org/<org>/runs/<run-id>",
      "dagster_cloud_graphql_url": "https://dagster.cloud/api/graphql",
      "callback_url": "https://your.service/ingest"
    }
}'
```

On completion, the workflow will POST the agent output to your `callback_url`.

You can also dispatch via the GitHub CLI:

```bash
gh workflow run trigger-agent.yml \
  --repo OWNER/REPO \
  --ref main \
  --field run_url="https://<domain>/org/<org>/runs/<run-id>" \
  --field dagster_cloud_graphql_url="https://dagster.cloud/api/graphql" \
  --field callback_url="https://your.service/ingest"
```
