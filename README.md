# dagster-diagnostic-agent

A diagnostic agent for Dagster.

## Requirements

- Python >=3.12
- uv (https://github.com/astral-sh/uv)

## Setup

Install uv and sync the project environment:

```bash
pip install uv
uv lock && uv sync
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
