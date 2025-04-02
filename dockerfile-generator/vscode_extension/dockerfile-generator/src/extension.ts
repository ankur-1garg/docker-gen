// vscode_extension/src/extension.ts

// The module 'vscode' contains the VS Code extensibility API
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

    console.log('Congratulations, your extension "mcp-dockerfile-generator" is now active!');

    // The command has been defined in the package.json file
    // Now provide the implementation with registerCommand
    // The commandId parameter must match the command field in package.json
    let disposable = vscode.commands.registerCommand('mcp-dockerfile-generator.generate', () => {
        // The code you place here will be executed every time your command is executed

        // Display a message box to the user
        vscode.window.showInformationMessage('Hello from MCP Dockerfile Generator!');

        // --- Placeholder for Day 16/17 ---
        console.log("TODO Day 16: Get user input (language, version, etc.)");
        console.log("TODO Day 16: Read configuration (server URL)");
        console.log("TODO Day 17: Call MCP Server API");
        console.log("TODO Day 17: Display result in new editor");
        // --- End Placeholder ---
    });

    // Add the command disposable to the context subscriptions
    // This ensures the command is cleaned up when the extension is deactivated
    context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {
     console.log('Extension "mcp-dockerfile-generator" is now deactivated.');
}