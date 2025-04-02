# mcp_server/app/api/v1/dockerfile.py (Corrected Version with Fixed get_base_image)

import re
from fastapi import APIRouter, Depends, status
from app.models.request import DockerfileRequest
from app.models.response import DockerfileResponse, BaseImage, ErrorResponse
from app.config import Config, get_config
from app.utils.logger import logger

# Import specific exceptions that this module might raise or encounter
from app.utils.exceptions import (
    UnsupportedLanguageError,
    AIResponseError,
    DockerfileGeneratorError # Base error for unexpected issues
)
# Import AI exceptions to let them bubble up
from app.core.ai_service import (
    get_gemini_dockerfile_suggestion,
    create_dockerfile_prompt,
    AIAuthenticationError,
    AIConnectionError,
    AIServiceError # Base AI error class
)

router = APIRouter()

@router.post("/generate-dockerfile",
             response_model=DockerfileResponse,
             responses={
                 400: {"model": ErrorResponse, "description": "Invalid input (e.g., unsupported language)"},
                 404: {"model": ErrorResponse, "description": "Mapping not found (if logic changes)"},
                 500: {"model": ErrorResponse, "description": "Internal Server Error (AI Response, Auth, Unexpected)"},
                 503: {"model": ErrorResponse, "description": "Service Unavailable (Config Error, AI Connection)"},
             })
async def generate_dockerfile(
    request: DockerfileRequest,
    config: Config = Depends(get_config)
):
    """
    Generate a Dockerfile using AI suggestions, replacing the base image
    with the company-specific Harbor path.
    """
    logger.info(f"Received request to generate Dockerfile for language: {request.language}, version: {request.version}")
    try:
        # Step 1: Determine generic base image (uses the FIXED function below)
        generic_base_image = get_base_image(request.language, request.version) # Call the fixed function
        logger.info(f"Determined generic base image: {generic_base_image}")

        # Step 2: Resolve Harbor path
        harbor_path = config.resolve_harbor_path(generic_base_image)
        logger.info(f"Resolved Harbor path: {harbor_path}")

        # Step 3: Construct the prompt for the AI service
        prompt = create_dockerfile_prompt(
            language=request.language, version=request.version,
            dependencies=request.dependencies, port=request.port,
            app_type=request.app_type, additional_instructions=request.additional_instructions,
            generic_base_image=generic_base_image
        )

        # Step 4: Call the AI service
        logger.info("Requesting Dockerfile suggestion from AI service...")
        ai_dockerfile_content = get_gemini_dockerfile_suggestion(prompt)
        logger.info("Successfully received AI suggestion.")

        # Step 5: Parse the AI response and replace the FROM line(s)
        modified_lines = []
        found_and_replaced = False
        from_pattern = re.compile(r"^\s*FROM\s+(\S+)", re.IGNORECASE)
        ai_lines = ai_dockerfile_content.splitlines()

        for line in ai_lines:
            match = from_pattern.match(line)
            # Use case-insensitive comparison for robustness
            if match and not found_and_replaced and match.group(1).strip().lower() == generic_base_image.lower():
                modified_lines.append(f"FROM {harbor_path}")
                found_and_replaced = True
                logger.info(f"Replaced FROM line using generic image '{generic_base_image}' with Harbor path.")
            else:
                modified_lines.append(line)

        if not found_and_replaced:
            err_msg = f"AI response processed, but failed to find and replace the expected generic FROM line ('FROM {generic_base_image}'). Check AI output format."
            logger.error(err_msg + f" Raw AI content: \n{ai_dockerfile_content}")
            raise AIResponseError(err_msg)

        final_dockerfile_content = "\n".join(modified_lines)

        # Step 6: Return the successful response
        logger.info(f"Successfully generated Dockerfile for language {request.language}.")
        return DockerfileResponse(
            status="success",
            dockerfile_content=final_dockerfile_content,
            base_image=BaseImage(
                generic=generic_base_image,
                harbor_path=harbor_path
            )
        )

    except (UnsupportedLanguageError, AIAuthenticationError, AIConnectionError, AIServiceError, AIResponseError) as e:
         raise e # Let specific errors bubble up to main handlers
    except Exception as e:
        logger.error(f"Unexpected internal error in generate_dockerfile endpoint: {e}", exc_info=True)
        raise DockerfileGeneratorError(f"An unexpected internal server error occurred processing the request: {e}") from e


# --- FIXED Helper function to determine generic base image name ---
def get_base_image(language: str, version: str = None) -> str:
    """
    Determine the appropriate generic base image name based on language and version.
    Handles different language conventions and defaults intelligently.
    Raises UnsupportedLanguageError if language is not mapped.
    """
    lang_lower = language.lower()

    # --- Python Logic ---
    if lang_lower == "python":
        if not version:
            image = "python:3.11-slim" # Default Python version if none provided
        # Check if user explicitly asked for a variant in the version string
        elif "-slim" in version or "-alpine" in version or "-buster" in version: # Add other common variants
             image = f"python:{version}" # Use the provided version directly
        else: # Assume slim if no variant specified by user
            image = f"python:{version}-slim"

    # --- Node Logic ---
    elif lang_lower == "node":
        if not version:
            image = "node:18-alpine" # Default Node version
        # Check if user explicitly asked for a variant
        elif "-alpine" in version or "-slim" in version or "-buster" in version: # Add other common variants
             image = f"node:{version}" # Use the provided version directly
        else: # Assume alpine if no variant specified
             image = f"node:{version}-alpine"

    # --- Java Logic ---
    elif lang_lower == "java":
        if not version:
             image = "openjdk:17-jdk-slim" # Default Java
        # Check if user explicitly asked for a variant
        elif "-jre" in version or "-jdk" in version or "-slim" in version: # Add other common variants
             image = f"openjdk:{version}" # Use directly (base name is openjdk)
        else: # Assume jdk-slim otherwise
             image = f"openjdk:{version}-jdk-slim"

    # --- Go Logic ---
    elif lang_lower == "go":
        if not version:
             image = "golang:1.20-alpine" # Default Go
        # Check if user explicitly asked for alpine
        elif "-alpine" in version:
             image = f"golang:{version}" # Use directly
        else: # Assume alpine otherwise
             image = f"golang:{version}-alpine"

    # --- Rust Logic ---
    elif lang_lower == "rust":
        if not version:
             image = "rust:1.68" # Default Rust
        else:
             image = f"rust:{version}" # Rust tags usually don't have variants like slim/alpine

    # --- Add other languages as needed ---
    # Example:
    # elif lang_lower == "ruby":
    #    # ... add logic for ruby ...

    else:
        # Language not explicitly handled above
        raise UnsupportedLanguageError(language=language)

    logger.debug(f"Mapping language '{language}' version '{version}' to generic base image '{image}'")
    return image