// vscode_extension/src/extension.ts

import * as vscode from "vscode";
import { getServerUrl } from "./utils/configuration";
// Import the API service function
import { generateDockerfileFromServer } from "./services/apiService";

export function activate(context: vscode.ExtensionContext) {
  console.log('Extension "mcp-dockerfile-generator" active!');

  let disposable = vscode.commands.registerCommand(
    "mcp-dockerfile-generator.generate",
    async () => {
      const serverUrl = getServerUrl();
      // Remove the initial message or keep it brief
      // vscode.window.showInformationMessage(`Using MCP Server URL: ${serverUrl}`);

      // --- Gather User Input (Keep code from Day 16) ---
      const language = await vscode.window.showInputBox({
        /* ... */
      });
      if (language === undefined) {
        return;
      } // Exit if cancelled
      const version = await vscode.window.showInputBox({
        /* ... */
      });
      const dependencies = await vscode.window.showInputBox({
        /* ... */
      });
      const portStr = await vscode.window.showInputBox({
        /* ... */
      });
      const port = portStr ? parseInt(portStr, 10) : undefined;
      const additionalInstructions = await vscode.window.showInputBox({
        /* ... */
      });

      // --- Prepare Payload ---
      const dependenciesList = dependencies
        ? dependencies
            .split(",")
            .map((d: string) => d.trim())
            .filter((d: string) => d.length > 0)
        : undefined;

      const payload = {
        language: language.trim(), // Ensure language has no extra spaces
        // Send null if version/deps/port/instructions are empty strings or undefined
        version: version || undefined, // Use || undefined to handle empty string from input
        dependencies: dependenciesList, // Already undefined if no input
        port: port, // Already undefined if no input
        // app_type: undefined, // Add if needed
        additional_instructions: additionalInstructions || undefined,
      };

      // --- Call API and Handle Response ---
      try {
        // Show some progress indication
        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: "Generating Dockerfile via MCP Server...",
            cancellable: false, // Making it cancellable adds complexity
          },
          async (progress) => {
            progress.report({ increment: 0, message: "Calling API..." });

            // Call the API Service (await the result)
            const dockerfileContent = await generateDockerfileFromServer(
              payload
            );

            progress.report({ increment: 50, message: "Opening result..." });

            // --- Success: Show content in new editor ---
            // Create a new untitled document with the content
            // Setting language explicitly helps with syntax highlighting
            const newDocument = await vscode.workspace.openTextDocument({
              content: dockerfileContent,
              language: "dockerfile", // Set language mode to Dockerfile
            });

            // Show the document in a new editor column
            await vscode.window.showTextDocument(
              newDocument,
              vscode.ViewColumn.Beside
            );

            progress.report({ increment: 100, message: "Done." });
            // Optional: Briefly show success message after progress disappears
            // setTimeout(() => vscode.window.showInformationMessage('Dockerfile generated successfully!'), 500);
          }
        );
      } catch (error) {
        // --- Error: Show error message ---
        // The error thrown by apiService should be user-friendly
        let errorMessage = "An unknown error occurred.";
        if (error instanceof Error) {
          errorMessage = error.message; // Use the message from the caught error
        }
        console.error("Caught error in command handler:", error); // Log the full error too
        vscode.window.showErrorMessage(
          `Failed to generate Dockerfile: ${errorMessage}`
        );
      }
    }
  );

  context.subscriptions.push(disposable);
}

export function deactivate() {
  console.log('Extension "mcp-dockerfile-generator" deactivated.');
}
