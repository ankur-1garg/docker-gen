// vscode_extension/src/utils/configuration.ts
import * as vscode from "vscode";

/**
 * Gets the configured MCP Server URL from VS Code settings.
 *
 * @returns The server URL string.
 */
export function getServerUrl(): string {
  // Get the configuration object for our extension
  const config = vscode.workspace.getConfiguration("mcp-dockerfile-generator");

  // Retrieve the value for the 'serverUrl' setting
  // The second argument is the default value if the setting is not found (redundant if default is set in package.json, but safe)
  const serverUrl = config.get<string>("serverUrl", "http://localhost:8000");

  // Basic validation or cleaning (e.g., remove trailing slash)
  return serverUrl.replace(/\/$/, ""); // Remove trailing slash if present
}

// Add functions here later to get other configurations if needed
