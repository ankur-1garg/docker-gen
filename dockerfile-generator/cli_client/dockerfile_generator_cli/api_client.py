# cli_client/dockerfile_generator_cli/api_client.py
import requests
from typing import Optional, List, Dict, Any
import json # Import json for potential error parsing

from .config import get_server_url # Get the helper to find the server URL

# Define potential custom exceptions for the client
class APIClientError(Exception):
    """Base exception for API client errors."""
    pass

class ConnectionError(APIClientError):
    """Raised for network-level errors connecting to the server."""
    pass

class ServerError(APIClientError):
    """Raised for non-successful (>=400) responses from the server."""
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Server returned error {status_code}: {detail}")


def call_mcp_api(
    language: str,
    version: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    port: Optional[int] = None,
    app_type: Optional[str] = None,
    instructions: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calls the MCP Server's /generate-dockerfile endpoint.

    Args:
        language: Programming language.
        version: Language version.
        dependencies: List of dependencies.
        port: Port to expose.
        app_type: Application type.
        instructions: Additional instructions.

    Returns:
        The JSON response dictionary from the server if successful.

    Raises:
        ConnectionError: If unable to connect to the server.
        ServerError: If the server returns a non-200 status code.
        APIClientError: For other request-related errors.
    """
    server_url = get_server_url()
    api_endpoint = f"{server_url}/api/v1/generate-dockerfile"

    # Construct the request payload, carefully handling None values
    payload: Dict[str, Any] = {"language": language}
    if version is not None:
        payload["version"] = version
    if dependencies is not None:
        payload["dependencies"] = dependencies
    if port is not None:
        payload["port"] = port
    if app_type is not None:
        payload["app_type"] = app_type
    if instructions is not None:
        # Use the key expected by the server model ('additional_instructions')
        payload["additional_instructions"] = instructions

    print(f"-> Calling MCP Server at: {api_endpoint}")
    print(f"   Payload: {json.dumps(payload)}") # Log the payload being sent

    try:
        response = requests.post(
            api_endpoint,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=90 # Add a timeout (e.g., 30 seconds)
        )

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # If successful (status code 200-299), parse and return JSON
        print(f"<- Server responded with status: {response.status_code}")
        return response.json()

    except requests.exceptions.ConnectionError as e:
        err_msg = f"Connection Error: Failed to connect to MCP server at {api_endpoint}. Is it running? Details: {e}"
        print(f"[Error] {err_msg}")
        raise ConnectionError(err_msg) from e
    except requests.exceptions.Timeout as e:
        err_msg = f"Timeout Error: Request to MCP server at {api_endpoint} timed out. Details: {e}"
        print(f"[Error] {err_msg}")
        raise ConnectionError(err_msg) from e
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        try:
            # Try to get detail from JSON response, otherwise use reason
            detail = e.response.json().get("detail", e.response.reason)
        except json.JSONDecodeError:
            detail = e.response.text # Fallback to raw text if not JSON
        err_msg = f"Server Error: MCP server returned status {status_code}. Detail: {detail}"
        print(f"[Error] {err_msg}")
        raise ServerError(status_code, detail) from e
    except requests.exceptions.RequestException as e:
        # Catch any other requests-related errors
        err_msg = f"Request Error: An unexpected error occurred during the request to {api_endpoint}. Details: {e}"
        print(f"[Error] {err_msg}")
        raise APIClientError(err_msg) from e
    except Exception as e:
        # Catch potentially other errors (like JSON parsing if response isn't JSON?)
        err_msg = f"Unexpected Error: An unexpected error occurred. Details: {e}"
        print(f"[Error] {err_msg}")
        raise APIClientError(err_msg) from e