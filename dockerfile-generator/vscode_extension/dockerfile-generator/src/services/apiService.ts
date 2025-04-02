// vscode_extension/src/services/apiService.ts
import axios, { AxiosError } from "axios";
import * as vscode from "vscode";
import { getServerUrl } from "../utils/configuration"; // Import config helper

// Interface matching the server's DockerfileRequest model (optional but good practice)
interface DockerfileRequestPayload {
  language: string;
  version?: string | null; // Allow null or undefined
  dependencies?: string[] | null;
  port?: number | null;
  app_type?: string | null; // Add if your server uses it
  additional_instructions?: string | null;
}

// Interface matching the server's successful DockerfileResponse model
interface DockerfileResponseSuccess {
  status: "success";
  dockerfile_content: string;
  base_image: {
    generic: string;
    harbor_path: string;
  };
}

// Interface matching the server's ErrorResponse model
interface DockerfileResponseError {
  status: "error";
  message: string;
  error_code?: string;
}

// Type guard to check for our specific error structure
function isDockerfileResponseError(obj: any): obj is DockerfileResponseError {
  return (
    typeof obj === "object" &&
    obj !== null &&
    obj.status === "error" &&
    typeof obj.message === "string"
  );
}

/**
 * Calls the MCP Server API to generate a Dockerfile.
 * @param payload Data collected from the user.
 * @returns The generated Dockerfile content string.
 * @throws An error with a user-friendly message if the API call fails.
 */
export async function generateDockerfileFromServer(
  payload: DockerfileRequestPayload
): Promise<string> {
  const serverUrl = getServerUrl();
  const apiUrl = `${serverUrl}/api/v1/generate-dockerfile`; // Ensure this path matches your server API

  console.log(`Calling MCP Server API: ${apiUrl}`);
  console.log("Payload:", JSON.stringify(payload));

  try {
    const response = await axios.post<DockerfileResponseSuccess>(
      apiUrl,
      payload,
      {
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        timeout: 90000, // Use milliseconds for axios timeout (e.g., 90 seconds)
      }
    );

    // Check if the response looks successful (axios only throws for >=400 by default)
    if (
      response.status === 200 &&
      response.data &&
      response.data.status === "success" &&
      response.data.dockerfile_content
    ) {
      console.log("API call successful. Received Dockerfile content.");
      return response.data.dockerfile_content;
    } else {
      // Handle unexpected successful status codes or missing data
      console.error("Unexpected successful response format:", response.data);
      throw new Error(
        `Received an unexpected response format from the server (Status: ${response.status}).`
      );
    }
  } catch (error) {
    console.error("Error calling MCP Server API:", error);

    // Handle different error types
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      if (axiosError.response) {
        // Server responded with an error status code (4xx, 5xx)
        const responseData = axiosError.response.data;
        // Try to parse error detail using our type guard
        if (isDockerfileResponseError(responseData)) {
          console.error(
            `Server error ${axiosError.response.status}: ${responseData.message} (Code: ${responseData.error_code})`
          );
          // Throw a more specific error message for the user
          throw new Error(
            `Server Error (${axiosError.response.status}): ${responseData.message}`
          );
        } else {
          // Fallback if error response doesn't match expected structure
          console.error(
            `Server error ${axiosError.response.status}:`,
            responseData
          );
          throw new Error(
            `Server returned an error (Status ${axiosError.response.status}). Check server logs for details.`
          );
        }
      } else if (axiosError.request) {
        // Request was made but no response received (network error, timeout)
        console.error("Network Error/Timeout:", axiosError.message);
        throw new Error(
          `Could not connect to the MCP server at ${serverUrl}. Please check if it's running and accessible.`
        );
      } else {
        // Something happened setting up the request
        console.error("Axios setup error:", axiosError.message);
        throw new Error(`Failed to send request: ${axiosError.message}`);
      }
    } else {
      // Non-axios error
      console.error("Non-axios error:", error);
      throw new Error(
        `An unexpected error occurred: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }
}
