# cli_client/dockerfile_generator_cli/config.py
import os
from dotenv import load_dotenv

# Load .env file from the current working directory OR the script's location
# This allows running the CLI from different places and still finding a potential .env
load_dotenv()

# Default server URL (can be overridden by environment variable)
# Users will need to set MCP_SERVER_URL in their environment or a local .env file
DEFAULT_MCP_SERVER_URL = "http://localhost:8000" # Default to local server during dev

def get_server_url() -> str:
    """Gets the MCP Server URL from env var or uses default."""
    url = os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL)
    # Ensure no trailing slash for consistency
    return url.rstrip('/')

# You could add more config loading logic here later (e.g., from ~/.config file)