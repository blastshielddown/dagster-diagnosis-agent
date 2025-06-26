"""
Configuration for Dagster Diagnosis Agent.
"""
from dotenv import load_dotenv
import os

# Load environment variables from a .env file if present
load_dotenv()

# Dagster Cloud settings
DAGSTER_CLOUD_API_TOKEN = os.environ.get("DAGSTER_CLOUD_API_TOKEN")
DAGSTER_CLOUD_GRAPHQL_URL = os.environ.get(
    "DAGSTER_CLOUD_GRAPHQL_URL", "https://dagster.cloud/api/graphql"
)

# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not DAGSTER_CLOUD_API_TOKEN:
    raise EnvironmentError(
        "DAGSTER_CLOUD_API_TOKEN environment variable is required"
    )
if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY environment variable is required"
    )
