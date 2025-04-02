# tests/test_config.py (Apply fixes for assertion count and no_match_no_tag expectation)

import unittest
import os
import yaml
from unittest.mock import patch, mock_open

# Adjust the import path based on running tests from the root 'mcp_server' directory
from app.config import Config, ConfigError
from app.utils.logger import logger # Optional: silence logger during tests if needed
import logging # Import logging if you want to silence the logger

# Disable logger spam during tests (optional)
logger.setLevel(logging.CRITICAL)

# Define sample YAML content for tests
SAMPLE_VALID_YAML = """
harbor_base_url: "harbor.test.local"
mappings:
  python: "base-images/python-base"
  python:3.11-slim: "prod/python:3.11-slim-v2"
  node:18: "dev/node:18.15.0"
  alpine: "public/alpine"
  nginx:1.23: "public/nginx:stable-1.23"
  "my-custom-app:v1.0": "apps/my-app:1.0-release"
"""

SAMPLE_NO_BASE_URL_YAML = """
mappings:
  python: "base/python"
"""

SAMPLE_EMPTY_YAML = ""

# Use a more robust invalid YAML
SAMPLE_INVALID_YAML = """
harbor_base_url: harbor.test.local
mappings: { this is definitely not valid yaml syntax } :
  python: base/python
"""

class TestConfig(unittest.TestCase):

    def setUp(self):
        """Create dummy config file path for tests."""
        self.test_config_path = "test_mapping.yaml"
        # Clean up any previous test file if it exists
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def tearDown(self):
        """Remove dummy config file after tests."""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def _create_test_yaml(self, content):
        """Helper to write content to the test YAML file."""
        with open(self.test_config_path, "w") as f:
            f.write(content)

    # --- Test Config Loading ---

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        self._create_test_yaml(SAMPLE_VALID_YAML)
        config = Config(config_path=self.test_config_path)

        self.assertEqual(config.harbor_base_url, "harbor.test.local")
        self.assertIn("python", config.mappings)
        self.assertIn("python:3.11-slim", config.mappings)
        self.assertEqual(config.mappings["python"], "base-images/python-base")
        # FIX 1: Assert count is 6
        self.assertEqual(len(config.mappings), 6)

    def test_load_config_file_not_found(self):
        """Test handling when the config file doesn't exist."""
        with self.assertRaises(ConfigError) as cm:
            Config(config_path="non_existent_file.yaml")
        self.assertIn("Configuration file not found", str(cm.exception))

    def test_load_empty_config(self):
        """Test loading an empty YAML file (should warn but not fail hard)."""
        self._create_test_yaml(SAMPLE_EMPTY_YAML)
        # Expect warnings in logs, but Config object should be created (empty)
        config = Config(config_path=self.test_config_path)
        self.assertEqual(config.harbor_base_url, "")
        self.assertEqual(config.mappings, {})

    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML format."""
        self._create_test_yaml(SAMPLE_INVALID_YAML)
        # This should now raise ConfigError wrapping YAMLError
        with self.assertRaises(ConfigError) as cm:
            Config(config_path=self.test_config_path)
        self.assertIn("Error parsing configuration file", str(cm.exception))

    def test_load_config_no_base_url(self):
        """Test loading config where harbor_base_url is missing (should warn)."""
        self._create_test_yaml(SAMPLE_NO_BASE_URL_YAML)
        # Expect warnings in logs, but object should load
        config = Config(config_path=self.test_config_path)
        self.assertEqual(config.harbor_base_url, "")
        self.assertIn("python", config.mappings)

    # --- Test Harbor Path Resolution ---

    @classmethod
    def setUpClass(cls):
        """Load config once for all resolution tests."""
        cls.shared_test_config_path = "shared_test_mapping.yaml"
        with open(cls.shared_test_config_path, "w") as f:
            f.write(SAMPLE_VALID_YAML)
        cls.config = Config(config_path=cls.shared_test_config_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up shared config file."""
        if os.path.exists(cls.shared_test_config_path):
            os.remove(cls.shared_test_config_path)

    def test_resolve_exact_match(self):
        """Test resolution when an exact image:tag is mapped."""
        resolved = self.config.resolve_harbor_path("python:3.11-slim")
        self.assertEqual(resolved, "harbor.test.local/prod/python:3.11-slim-v2")

    def test_resolve_base_name_match(self):
        """Test resolution using base name mapping when tag isn't exact match."""
        resolved = self.config.resolve_harbor_path("python:3.10")
        self.assertEqual(resolved, "harbor.test.local/base-images/python-base:3.10")

    def test_resolve_base_name_match_no_tag_input(self):
        """Test resolution using base name mapping when no tag is provided."""
        resolved = self.config.resolve_harbor_path("python")
        # This test should now pass with the updated resolve_harbor_path logic
        self.assertEqual(resolved, "harbor.test.local/base-images/python-base:latest")

    def test_resolve_no_match(self):
        """Test resolution when neither exact nor base name is mapped."""
        resolved = self.config.resolve_harbor_path("ubuntu:22.04")
        self.assertEqual(resolved, "harbor.test.local/library/ubuntu:22.04")

    def test_resolve_no_match_no_tag_input(self):
        """Test resolution when no match and no tag provided."""
        resolved = self.config.resolve_harbor_path("redis")
        # FIX 3: Expect ':latest' tag to be appended by default logic
        self.assertEqual(resolved, "harbor.test.local/library/redis:latest")

    def test_resolve_match_with_colon_in_name(self):
        """Test resolution for names that might include colons themselves."""
        resolved = self.config.resolve_harbor_path("my-custom-app:v1.0")
        self.assertEqual(resolved, "harbor.test.local/apps/my-app:1.0-release")

    def test_resolve_no_base_url_configured(self):
        """Test resolution behavior when harbor_base_url is missing."""
        self._create_test_yaml(SAMPLE_NO_BASE_URL_YAML)
        config_no_base = Config(config_path=self.test_config_path)
        resolved = config_no_base.resolve_harbor_path("python:3.11")
        self.assertEqual(resolved, "python:3.11")


if __name__ == '__main__':
    unittest.main()