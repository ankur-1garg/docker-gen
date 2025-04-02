# mcp_server/app/core/ai_service.py (Corrected Exception Handling for Google Gemini)

import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions # Import Google exceptions
from dotenv import load_dotenv
from typing import List, Optional # Import these for the example prompt function
from app.utils.logger import logger

# Load environment variables from .env file
load_dotenv()

# --- Configure the Google Generative AI Client ---
GOOGLE_API_KEY = os.getenv("gemini_API_KEY") # Use the name from your .env file
is_configured = False

if not GOOGLE_API_KEY:
    logger.warning("Google API Key (expected as 'gemini_API_KEY' in .env) not found. AI calls will fail.")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        is_configured = True
        logger.info("Google Generative AI client configured successfully.")
        # Optional: You could add a basic test call here if needed, but might slow startup
    except Exception as e:
        logger.error(f"Failed to configure Google Generative AI client: {e}", exc_info=True)
        # is_configured remains False

# --- Define Custom Exceptions (can reuse from previous OpenAI version) ---
class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass

class AIConnectionError(AIServiceError):
    """Raised for connection or availability issues with the AI service."""
    pass

class AIAuthenticationError(AIServiceError):
    """Raised for authentication issues with the AI service."""
    pass

# --- Function to call Gemini API ---
def get_gemini_dockerfile_suggestion(prompt: str, model_name: str = "models/gemini-1.5-pro-latest") -> str:
    """
    Sends a prompt to the Google Gemini API and returns the AI's response text.

    Args:
        prompt: The detailed prompt for the AI.
        model_name: The Gemini model to use (default: gemini-pro).

    Returns:
        The content of the AI's response as a string.

    Raises:
        AIAuthenticationError: If authentication fails (PermissionDenied).
        AIConnectionError: If there's a connection or API issue (ServiceUnavailable, ResourceExhausted).
        AIServiceError: For other Google API or unexpected errors, or if the client isn't configured.
    """
    if not is_configured:
        logger.error("Google Generative AI client is not configured. Cannot make AI calls.")
        raise AIServiceError("Google client is not configured. Check API key and logs.")

    logger.info(f"Sending prompt to Google Gemini model: {model_name}")
    logger.debug(f"Prompt:\n---\n{prompt}\n---")

    try:
        model = genai.GenerativeModel(model_name)

        # Configure safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Make the API call
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3
            ),
            safety_settings=safety_settings
        )

        # Check if the response was blocked or didn't generate text
        if not response.candidates:
             logger.warning(f"Gemini response was empty or blocked. Feedback: {response.prompt_feedback}")
             # Extract the reason if possible
             block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
             raise AIServiceError(f"AI response was blocked or empty. Reason: {block_reason}. Safety feedback: {response.prompt_feedback}")

        # Extract text
        ai_content = response.text

        logger.info("Received response from Google Gemini.")
        logger.debug(f"Raw AI Response Content:\n---\n{ai_content}\n---")

        # Simple cleaning
        cleaned_content = ai_content.strip().removeprefix("```dockerfile").removesuffix("```").strip()

        return cleaned_content

    # --- CORRECTED Exception Handling ---
    except google_exceptions.PermissionDenied as e:
        logger.error(f"Google API Permission Denied Error: {e}")
        raise AIAuthenticationError(f"Google API authentication failed (Permission Denied). Check your API key and permissions. Original error: {e}") from e
    except google_exceptions.ResourceExhausted as e:
         logger.error(f"Google API Rate Limit/Quota Error: {e}")
         raise AIConnectionError(f"Google API rate limit or quota exceeded. Original error: {e}") from e
    except google_exceptions.ServiceUnavailable as e: # CORRECTED: Use ServiceUnavailable
         logger.error(f"Google API Service Unavailable Error: {e}")
         raise AIConnectionError(f"Google API service is unavailable. Please try again later. Original error: {e}") from e
    except google_exceptions.InvalidArgument as e: # ADDED: Catch invalid arguments
        logger.error(f"Google API Invalid Argument Error: {e}")
        raise AIServiceError(f"Invalid argument provided to Google API (e.g., model name, safety setting). Original error: {e}") from e
    except google_exceptions.GoogleAPIError as e: # Catch-all for other Google errors
        logger.error(f"Google API Error: {e}")
        raise AIServiceError(f"A Google API error occurred: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during Google Gemini API call: {e}", exc_info=True)
        raise AIServiceError(f"An unexpected error occurred while contacting the Google AI service: {e}") from e
    # --- End of CORRECTED Exception Handling ---


# --- Example Basic Prompt Construction (Same as before, generally compatible) ---
# The actual prompt will be built dynamically in the API endpoint (Day 7).
def create_dockerfile_prompt(
    language: str,
    version: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    port: Optional[int] = None,
    app_type: Optional[str] = None,
    additional_instructions: Optional[str] = None,
    generic_base_image: str = "GENERIC_BASE_IMAGE_PLACEHOLDER" # Placeholder for base image
) -> str:
    """
    Constructs a basic prompt for the AI Dockerfile generation.
    (This is an example; the real logic might live in the endpoint or another helper)
    """
    prompt_lines = [
        f"Generate a concise and best-practice Dockerfile for a '{language}' application."
    ]
    if version:
        prompt_lines.append(f"Use language version '{version}'.")
    if app_type:
        prompt_lines.append(f"The application type is '{app_type}'.")

    # IMPORTANT: Tell the AI to use the *generic* name, we will replace it later
    prompt_lines.append(f"Use the base image '{generic_base_image}'. Do not use any registry prefix in the FROM line.")

    if dependencies:
        deps_str = ", ".join(dependencies)
        if language.lower() == "python":
             prompt_lines.append(f"The application requires these dependencies: {deps_str}. Install them using pip, preferably from a requirements.txt file.")
        elif language.lower() == "node":
             prompt_lines.append(f"The application requires these dependencies: {deps_str}. Install them using npm from a package.json file.")
        else:
            prompt_lines.append(f"The application requires these dependencies: {deps_str}.")

    if port:
        prompt_lines.append(f"The application needs to expose port {port}.")

    prompt_lines.append("Ensure the Dockerfile copies necessary application code (e.g., using `COPY . .`).")
    prompt_lines.append("Set a reasonable default command (CMD or ENTRYPOINT) to run the application.")

    if additional_instructions:
        prompt_lines.append(f"Follow these additional instructions: {additional_instructions}")

    prompt_lines.append("\nOutput only the raw Dockerfile content, without any explanation or markdown formatting like ```dockerfile.")

    return "\n".join(prompt_lines)