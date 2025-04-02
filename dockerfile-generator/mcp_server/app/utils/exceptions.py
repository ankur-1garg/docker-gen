# mcp_server/app/utils/exceptions.py

# Import base AI exceptions to potentially handle them distinctly if needed,
# or just know they exist when handling AIServiceError.
from app.core.ai_service import AIAuthenticationError, AIConnectionError # noqa - Import even if not directly used here, for awareness

# Base exception for our application
class DockerfileGeneratorError(Exception):
    """Base class for exceptions in this application."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "GENERATOR_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code # Add an error code for client-side handling
        super().__init__(message)

# Configuration related errors
class ConfigurationError(DockerfileGeneratorError):
    """Errors related to loading or accessing configuration."""
    def __init__(self, message: str):
        # Service Unavailable if essential config is broken
        super().__init__(message, status_code=503, error_code="CONFIG_ERROR")

# Harbor path resolution errors (Define even if not raised yet)
class HarborPathNotFoundError(DockerfileGeneratorError):
    """Raised when a mapping for a requested image cannot be found."""
    def __init__(self, image_name: str):
        message = f"No Harbor mapping configuration found for image: {image_name}"
        # 404 Not Found indicating the 'resource' (mapping) is missing
        super().__init__(message, status_code=404, error_code="MAPPING_NOT_FOUND")
        self.image_name = image_name

# Base Image selection errors
class UnsupportedLanguageError(DockerfileGeneratorError):
    """Raised when a requested language isn't supported for base image selection."""
    def __init__(self, language: str):
        message = f"The requested language '{language}' is not supported for base image selection."
        # 400 Bad Request as it's invalid user input
        super().__init__(message, status_code=400, error_code="UNSUPPORTED_LANGUAGE")
        self.language = language

# AI Service related errors
class AIServiceInteractionError(DockerfileGeneratorError):
    """Raised for general issues during AI service interaction."""
    def __init__(self, message: str, original_exception: Exception | None = None):
        # Map to Service Unavailable as the backend AI dependency failed
        super().__init__(message, status_code=503, error_code="AI_SERVICE_ERROR")
        self.original_exception = original_exception

class AIResponseError(DockerfileGeneratorError):
    """Raised when the AI response is invalid or unusable (e.g., missing FROM line)."""
    def __init__(self, message: str):
        # Internal Server Error as the backend failed to process AI output
        super().__init__(message, status_code=500, error_code="AI_RESPONSE_INVALID")