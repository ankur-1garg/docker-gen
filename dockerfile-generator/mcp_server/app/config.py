# mcp_server/app/config.py (Updated for Day 12)

import os
import yaml
from typing import Dict, Any
from app.utils.logger import logger
from fastapi import HTTPException, status # Keep for get_config

# Import the custom exception
from app.utils.exceptions import ConfigurationError

class Config:
    def __init__(self, config_path: str = "harbor_mapping.yaml"):
        """
        Initialize and load configuration.
        Raises ConfigurationError on critical load failures.
        """
        self.harbor_base_url: str = ""
        self.mappings: Dict[str, str] = {}

        effective_config_path = os.environ.get("HARBOR_MAPPING_PATH", config_path)
        logger.info(f"Attempting to load configuration from: {effective_config_path}")

        try:
            self._load_config(effective_config_path)
        except Exception as e:
            # Log and re-raise any exception during load as ConfigurationError if not already
            if not isinstance(e, ConfigurationError):
                err_msg = f"Failed to initialize configuration object: {e}"
                logger.critical(err_msg, exc_info=True)
                raise ConfigurationError(err_msg) from e
            else:
                # If it's already a ConfigurationError, just let it propagate
                raise e


    def _load_config(self, file_path: str):
        """
        Load configuration from the specified YAML file.
        Raises ConfigurationError on critical file/parse errors or missing base URL.
        """
        try:
            with open(file_path, "r") as file:
                config_data = yaml.safe_load(file)
                if not config_data:
                    logger.warning(f"Configuration file '{file_path}' is empty.")
                    # Treat empty file same as missing base URL - critical
                    raise ConfigurationError(f"Configuration file '{file_path}' is empty or invalid.")

                # Extract harbor base URL - CRITICAL
                self.harbor_base_url = config_data.get("harbor_base_url", "")
                if not self.harbor_base_url:
                    err_msg = f"'harbor_base_url' not found in configuration file: {file_path}"
                    logger.critical(err_msg)
                    raise ConfigurationError(err_msg) # RAISE
                else:
                     logger.info(f"Harbor Base URL set to: {self.harbor_base_url}")

                # Extract mappings (Warn if missing, but don't fail startup for this)
                self.mappings = config_data.get("mappings", {})
                if not self.mappings:
                    logger.warning(f"No image mappings found in configuration file: {file_path}")
                else:
                    logger.info(f"Loaded {len(self.mappings)} image mappings.")

        except FileNotFoundError as e:
            err_msg = f"Configuration file not found at '{file_path}'."
            logger.critical(err_msg)
            raise ConfigurationError(err_msg) from e # WRAP
        except yaml.YAMLError as e:
            err_msg = f"Error parsing YAML configuration file '{file_path}': {e}"
            logger.critical(err_msg)
            raise ConfigurationError(err_msg) from e # WRAP
        except Exception as e:
            # Catch any other unexpected errors during file processing
            err_msg = f"Unexpected error loading configuration content from '{file_path}': {e}"
            logger.critical(err_msg, exc_info=True)
            raise ConfigurationError(err_msg) from e # WRAP


    def resolve_harbor_path(self, generic_image_name: str) -> str:
        """
        Resolve a generic image name to a full Harbor-specific path.
        (Logic unchanged for Day 12, but could raise HarborPathNotFoundError if needed)
        """
        if not self.harbor_base_url:
            # This state shouldn't be reachable if __init__ raises ConfigurationError correctly
            logger.error(f"BUG: Attempted to resolve path for '{generic_image_name}' but harbor_base_url is not set.")
            # Raise an error here as well, as it indicates a problem
            raise ConfigurationError("Cannot resolve path: harbor_base_url is missing, configuration load likely failed.")

        # Determine base_name and tag first
        input_has_tag = ":" in generic_image_name
        if input_has_tag:
            parts = generic_image_name.split(":", 1)
            base_name = parts[0]
            tag = parts[1]
        else:
            base_name = generic_image_name
            tag = "latest" # Default tag if none provided

        # 1. Check for exact match (image:tag or image_without_tag)
        if generic_image_name in self.mappings:
            harbor_specific_part = self.mappings[generic_image_name]
            if not input_has_tag and ":" not in harbor_specific_part:
                 full_path = f"{self.harbor_base_url.rstrip('/')}/{harbor_specific_part.lstrip('/')}:{tag}"
                 logger.debug(f"Exact mapping found for '{generic_image_name}', appended default tag '{tag}': {full_path}")
            else:
                 full_path = f"{self.harbor_base_url.rstrip('/')}/{harbor_specific_part.lstrip('/')}"
                 logger.debug(f"Exact mapping found for '{generic_image_name}': {full_path}")
            return full_path

        # 2. Check for base name match only if exact match failed
        if base_name in self.mappings:
            harbor_specific_part = self.mappings[base_name]
            if ":" in harbor_specific_part:
                full_path = f"{self.harbor_base_url.rstrip('/')}/{harbor_specific_part.lstrip('/')}"
                logger.debug(f"Base name mapping for '{base_name}' found (path includes tag): {full_path}")
            else:
                full_path = f"{self.harbor_base_url.rstrip('/')}/{harbor_specific_part.lstrip('/')}:{tag}"
                logger.debug(f"Base name mapping for '{base_name}' found, appending tag '{tag}': {full_path}")
            return full_path

        # 3. No mapping found - construct default path
        logger.warning(f"No mapping found for '{generic_image_name}'. Constructing default path using 'library' scope.")
        default_path = f"{self.harbor_base_url.rstrip('/')}/library/{base_name}:{tag}"
        # If reaching here without finding any mapping isn't allowed, you would:
        # raise HarborPathNotFoundError(image_name=generic_image_name)
        return default_path


# == Dependency Injection Setup ==
config: Config | None = None
try:
    config = Config()
    logger.info("Configuration loaded successfully during module import.")
except ConfigurationError as e: # Catch specific config error
    logger.critical(f"CRITICAL CONFIGURATION ERROR during module import: {e}. Application startup failed.")
    # config remains None. The get_config dependency will raise an error later.
except Exception as e: # Catch other unexpected init errors
    logger.critical(f"Unexpected error during configuration initialization: {e}", exc_info=True)
    # config remains None


def get_config() -> Config:
    """
    FastAPI dependency function to get the shared Config instance.
    Raises HTTPException 503 if config failed to load during startup.
    """
    if config is None:
        logger.error("Dependency 'get_config' called but configuration object is None.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server configuration is unavailable. Please check server startup logs."
        )
    return config