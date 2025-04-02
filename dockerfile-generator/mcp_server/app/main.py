# mcp_server/app/main.py (Updated for Day 12)

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.docker_file import router as dockerfile_router
from app.config import config # Import config to check during startup
from app.models.response import ErrorResponse # Use our standard error model
from app.utils.logger import logger

# Import custom exceptions and AI exceptions to handle them
from app.utils.exceptions import (
    DockerfileGeneratorError,
    ConfigurationError,
    HarborPathNotFoundError,
    UnsupportedLanguageError,
    AIResponseError
    # AIServiceInteractionError could be caught by DockerfileGeneratorError handler
)
from app.core.ai_service import ( # Import specific AI errors
    AIAuthenticationError,
    AIConnectionError,
    AIServiceError # Base AI error if not caught specifically
)

# --- Check critical config during startup ---
if config is None:
    logger.critical("FATAL: Configuration object failed to initialize during application startup. Check config file and logs. Exiting.")
    # In a real scenario, you might want the application to fail hard here
    # For simplicity in dev, we let it continue, but requests needing config will fail.
    # import sys
    # sys.exit(1)
else:
     logger.info("Application configuration loaded/checked during startup.")


# --- Create FastAPI App ---
app = FastAPI(
    title="Dockerfile Generator",
    description="Service that generates Dockerfiles with company-specific Harbor paths",
    version="0.1.0",
    # Add OpenAPI URL if needed, e.g., for proxies
    # openapi_url="/api/v1/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors for request bodies/params."""
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(map(str, error['loc'])) # Make field path readable (e.g., body -> dependencies -> 0)
        message = error['msg']
        error_messages.append(f"Field {field}: {message}")
    detail = "Request validation failed. Details: " + "; ".join(error_messages)
    logger.warning(f"RequestValidationError: {detail}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(status="error", message=detail, error_code="VALIDATION_ERROR").dict(),
    )

@app.exception_handler(UnsupportedLanguageError)
async def unsupported_language_handler(request: Request, exc: UnsupportedLanguageError):
    """Handles errors for unsupported languages."""
    logger.warning(f"UnsupportedLanguageError caught: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code, # 400
        content=ErrorResponse(status="error", message=exc.message, error_code=exc.error_code).dict(),
    )

@app.exception_handler(HarborPathNotFoundError)
async def harbor_path_not_found_handler(request: Request, exc: HarborPathNotFoundError):
    """Handles errors when Harbor mapping is missing (if raised)."""
    logger.warning(f"HarborPathNotFoundError caught: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code, # 404
        content=ErrorResponse(status="error", message=exc.message, error_code=exc.error_code).dict(),
    )

@app.exception_handler(AIResponseError)
async def ai_response_error_handler(request: Request, exc: AIResponseError):
    """Handles errors related to invalid/unusable AI responses."""
    logger.error(f"AIResponseError caught: {exc.message}", exc_info=True) # Log details
    return JSONResponse(
        status_code=exc.status_code, # 500
        content=ErrorResponse(status="error", message=exc.message, error_code=exc.error_code).dict(),
    )

@app.exception_handler(AIConnectionError)
async def ai_connection_error_handler(request: Request, exc: AIConnectionError):
    """Handles AI service connection/availability/rate limit errors."""
    logger.error(f"AIConnectionError caught: {exc.message}", exc_info=True) # Log details
    # Return a generic 503 error to the client
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(status="error", message="The AI service is currently unavailable or rate limited. Please try again later.", error_code="AI_SERVICE_UNAVAILABLE").dict(),
    )

@app.exception_handler(AIAuthenticationError)
async def ai_auth_error_handler(request: Request, exc: AIAuthenticationError):
    """Handles AI service authentication errors (likely server config issue)."""
    # Log the detailed error but return a generic message to the user
    logger.error(f"AIAuthenticationError caught: {exc.message}", exc_info=True) # Log details
    # Return a generic 500 error as client cannot fix this
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(status="error", message="AI service authentication failed. Please contact the administrator.", error_code="AI_AUTH_ERROR").dict(),
    )

# Handler for our base custom error - catches ConfigurationError etc.
@app.exception_handler(DockerfileGeneratorError)
async def dockerfile_generator_exception_handler(request: Request, exc: DockerfileGeneratorError):
    """Handles base application errors and ConfigurationError."""
    logger.error(f"DockerfileGeneratorError caught: Status={exc.status_code}, Code={exc.error_code}, Message={exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(status="error", message=exc.message, error_code=exc.error_code).dict(),
    )

# Keep the generic 500 handler for truly unexpected errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handles any unexpected exceptions not caught by specific handlers."""
    logger.critical(f"Unhandled Exception caught by generic handler: {exc}", exc_info=True) # Log stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            message="An unexpected internal server error occurred.",
            error_code="UNEXPECTED_SERVER_ERROR"
        ).dict(),
    )

# --- Include Routers ---
app.include_router(
    dockerfile_router,
    prefix="/api/v1",
    tags=["Dockerfile Generation"] # Add a tag for Swagger UI
)

# --- Root/Health endpoints ---
@app.get("/", tags=["Status"])
async def root():
    """Root endpoint providing basic service info."""
    return {"message": "Dockerfile Generator MCP Server is running", "version": app.version}

@app.get("/health", tags=["Status"], response_model=dict)
async def health():
    """Simple health check endpoint."""
    # Could add checks here for DB, AI service connectivity etc. if needed later
    return {"status": "healthy"}