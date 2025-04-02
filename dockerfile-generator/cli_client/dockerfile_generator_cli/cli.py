# cli_client/dockerfile_generator_cli/cli.py
import typer
from typing_extensions import Annotated
from typing import List, Optional
from pathlib import Path
import sys

from .api_client import call_mcp_api, APIClientError, ConnectionError, ServerError
from pathlib import Path # Make sure this is imported

# ---> THIS LINE MUST EXIST <---
app = typer.Typer(
    name="mcp-dockergen",
    help="CLI tool to generate Dockerfiles using the MCP Server.",
    add_completion=True
)
# Keep app instance and Option definitions as they were
# --- Define Command-Line Options (Corrected Annotated Usage) ---
LanguageOption = Annotated[
    str, # <-- Type Argument
    typer.Option("--language", "-l", help="Programming language (e.g., python, node).", prompt="Enter the programming language") # <-- Annotation Argument
]
VersionOption = Annotated[
    Optional[str], # <-- Type Argument
    typer.Option("--version", "-v", help="Language version (e.g., 3.11, 18).") # <-- Annotation Argument
]
DependenciesStrOption = Annotated[
    Optional[str], # <-- Type Argument
    typer.Option("--deps", "-d", help="Comma-separated list of dependencies (e.g., flask,requests).") # <-- Annotation Argument
]
PortOption = Annotated[
    Optional[int], # <-- Type Argument
    typer.Option("--port", "-p", help="Port to expose in the Dockerfile.") # <-- Annotation Argument
]
AppTypeOption = Annotated[
    Optional[str], # <-- Type Argument
    typer.Option("--app-type", "-t", help="Type of application (e.g., web, cli, api).") # <-- Annotation Argument
]
AdditionalInstructionsOption = Annotated[
    Optional[str], # <-- Type Argument
    typer.Option("--instructions", "-i", help="Additional instructions for the AI.") # <-- Annotation Argument
]
OutputFileOption = Annotated[
    Optional[Path], # <-- Type Argument (Make sure 'from pathlib import Path' is at the top)
    typer.Option( # <-- Annotation Argument (Can be multi-line)
        "--output",
        "-o",
        help="Path to save the generated Dockerfile (prints to console if omitted).",
        writable=True,
        resolve_path=True
        )
]


# --- Define the 'generate' Command (Modified for Day 11) ---
@app.command()
def generate(
    language: LanguageOption,
    version: VersionOption = None,
    dependencies_str: DependenciesStrOption = None,
    port: PortOption = None,
    app_type: AppTypeOption = None,
    instructions: AdditionalInstructionsOption = None,
    output_file: OutputFileOption = None, # This is the pathlib.Path object or None
):
    """
    Generates a Dockerfile by calling the MCP server.
    """
    # --- Input processing (Keep from Day 10) ---
    typer.echo("Starting Dockerfile generation...")
    typer.echo(f"  Language: {language}")

    dependencies: Optional[List[str]] = None
    if dependencies_str:
        dependencies = [dep.strip() for dep in dependencies_str.split(',') if dep.strip()]
        if dependencies:
             typer.echo(f"  Dependencies: {dependencies}")

    if port:
        typer.echo(f"  Port: {port}")
    if app_type:
        typer.echo(f"  App Type: {app_type}")
    if instructions:
        typer.echo(f"  Instructions: {instructions}")
    if output_file:
         # output_file is already a resolved Path object due to typer.Option setup
         typer.echo(f"  Output File: {output_file}")

    # --- API Call (Keep from Day 10) ---
    typer.echo("\nAttempting to call MCP Server...")
    try:
        response_data = call_mcp_api(
            language=language,
            version=version,
            dependencies=dependencies,
            port=port,
            app_type=app_type,
            instructions=instructions
        )
        # Simple check if response looks okay before processing
        if not response_data or response_data.get("status") != "success":
             typer.secho(f"\nReceived non-successful or unexpected response from server: {response_data}", fg=typer.colors.YELLOW, err=True)
             raise typer.Exit(code=1)

        dockerfile_content = response_data.get("dockerfile_content")
        if dockerfile_content is None:
             typer.secho(f"\nServer response missing 'dockerfile_content'.", fg=typer.colors.RED, err=True)
             raise typer.Exit(code=1)

        # --- Output Handling (Day 11 Implementation) ---
        if output_file:
            # Write to the specified file (output_file is a pathlib.Path object)
            try:
                # Use write_text for simple text writing, ensures proper encoding handling (defaults to UTF-8)
                output_file.write_text(dockerfile_content, encoding='utf-8')
                typer.secho(f"\nSuccessfully wrote Dockerfile to: {output_file}", fg=typer.colors.GREEN)
            except (IOError, OSError) as e: # Catch potential file system errors
                typer.secho(f"\nError writing to file {output_file}: {e}", fg=typer.colors.RED, err=True)
                raise typer.Exit(code=1)
        else:
            # Print to standard output (console)
            typer.echo("\n--- Generated Dockerfile ---")
            typer.echo(dockerfile_content)
            typer.echo("--------------------------")
            typer.secho("\nSuccessfully generated Dockerfile.", fg=typer.colors.GREEN)


    # --- Error Handling (Keep from Day 10) ---
    except ConnectionError as e:
        typer.secho(f"\nError connecting to MCP server: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except ServerError as e:
        typer.secho(f"\nError from MCP server (HTTP {e.status_code}): {e.detail}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except APIClientError as e:
        typer.secho(f"\nAPI Client Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except typer.Exit:
         # Don't capture typer.Exit exceptions, let them exit gracefully
         raise
    except Exception as e:
        typer.secho(f"\nAn unexpected error occurred in the CLI: {e}", fg=typer.colors.RED, err=True)
        # Consider logging traceback here for debugging complex errors
        # import traceback
        # traceback.print_exc()
        raise typer.Exit(code=1)


# --- Other commands and entry point (Keep as before) ---
@app.command()
def check_server(): ...

if __name__ == "__main__": ...