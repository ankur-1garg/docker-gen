# We can now potentially remove this file if all logic stays within Config
# OR keep it as a thin wrapper if we anticipate more complex resolution logic later.
# For demonstration, let's keep it and show dependency usage.

from fastapi import Depends 
from app.config import Config, get_config # Import Config class and the dependency function
from app.utils.logger import logger

# We don't strictly *need* this function anymore if we call config.resolve directly,
# but it can be useful as an abstraction layer.
def resolve_harbor_path_from_config(
    generic_image_name: str, 
    config: Config = Depends(get_config) # Inject the config instance
) -> str:
    """
    Resolves the Harbor path using the injected configuration.

    Args:
        generic_image_name: The generic image name (e.g., "python:3.11-slim")
        config: The application configuration object (injected by FastAPI).

    Returns:
        The full Harbor path for the image.
    """
    logger.info(f"Core resolver resolving: {generic_image_name}")
    return config.resolve_harbor_path(generic_image_name)