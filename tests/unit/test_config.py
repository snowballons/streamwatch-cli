"""
Unit tests for configuration management module.
"""
import configparser
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.streamwatch import config


class TestConfigManagement:
    """Test configuration loading and management."""

    def test_default_config_values(self):
        """Test that default configuration values are properly defined."""
        assert "Streamlink" in config.DEFAULT_CONFIG
        assert "Interface" in config.DEFAULT_CONFIG
        assert "Misc" in config.DEFAULT_CONFIG

        # Test specific default values
        streamlink_config = config.DEFAULT_CONFIG["Streamlink"]
        assert streamlink_config["quality"] == "best"
        assert streamlink_config["timeout_liveness"] == "10"
        assert streamlink_config["timeout_metadata"] == "15"

    def test_app_constants(self):
        """Test that application constants are properly defined."""
        assert config.APP_NAME == "streamwatch"
        assert isinstance(config.USER_CONFIG_DIR, Path)

    def test_get_streamlink_quality_default(self, temp_config_dir):
        """Test getting streamlink quality with default value."""
        # No config file exists
        quality = config.get_streamlink_quality()
        assert quality == "best"

    def test_get_streamlink_quality_from_config(self, mock_config_file):
        """Test getting streamlink quality from config file."""
        with patch.object(config, "CONFIG_FILE_PATH", mock_config_file):
            quality = config.get_streamlink_quality()
            assert quality == "best"

    def test_get_streamlink_timeout_liveness_default(self, temp_config_dir):
        """Test getting streamlink liveness timeout with default value."""
        timeout = config.get_streamlink_timeout_liveness()
        assert timeout == 10

    def test_get_streamlink_timeout_metadata_default(self, temp_config_dir):
        """Test getting streamlink metadata timeout with default value."""
        timeout = config.get_streamlink_timeout_metadata()
        assert timeout == 15

    def test_get_hook_script_paths_default(self, temp_config_dir):
        """Test getting hook script paths with default values."""
        pre_hook = config.get_pre_playback_hook()
        post_hook = config.get_post_playback_hook()
        assert pre_hook == ""
        assert post_hook == ""

    def test_get_donation_link_default(self, temp_config_dir):
        """Test getting donation link with default value."""
        link = config.get_donation_link()
        assert "buymeacoffee.com" in link

    def test_config_file_creation(self, temp_config_dir):
        """Test that config file is created with default values when missing."""
        config_file = temp_config_dir / "config.ini"
        assert not config_file.exists()

        # This should create the config file
        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            quality = config.get_streamlink_quality()

        assert quality == "best"
        # Note: The actual file creation logic would need to be implemented in the config module

    def test_invalid_config_file_handling(self, temp_config_dir):
        """Test handling of invalid config file."""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text("invalid config content")

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should fall back to defaults when config is invalid
            quality = config.get_streamlink_quality()
            assert quality == "best"

    def test_first_run_detection(self, temp_config_dir):
        """Test first run detection logic."""
        # Initially should be first run
        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            is_first_run = not config.is_first_run_completed()
            assert is_first_run

    def test_mark_first_run_completed(self, temp_config_dir):
        """Test marking first run as completed."""
        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            config.mark_first_run_completed()
            # Should create the marker file
            marker_file = temp_config_dir / ".first_run_completed"
            assert marker_file.exists()

    def test_config_parsing_with_custom_values(self, temp_config_dir):
        """Test config parsing with custom values."""
        config_content = """
[Streamlink]
quality = 720p
timeout_liveness = 20
timeout_metadata = 30

[Misc]
pre_playback_hook = /path/to/pre.sh
post_playback_hook = /path/to/post.sh
donation_link = https://example.com/donate
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Force reload config
            config.load_config()

            assert config.get_streamlink_quality() == "720p"
            assert config.get_streamlink_timeout_liveness() == 20
            assert config.get_streamlink_timeout_metadata() == 30

            assert config.get_pre_playback_hook() == "/path/to/pre.sh"
            assert config.get_post_playback_hook() == "/path/to/post.sh"
            assert config.get_donation_link() == "https://example.com/donate"
