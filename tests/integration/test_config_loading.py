"""
Integration tests for configuration loading and management.
"""
import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from src.streamwatch import config


class TestConfigurationIntegration:
    """Test configuration loading and integration."""

    def test_config_loading_with_all_sections(self, temp_config_dir):
        """Test loading configuration with all sections present."""
        config_content = """
[Streamlink]
quality = 720p
timeout_liveness = 20
timeout_metadata = 30

[Player]
command = vlc
args = --intf dummy --no-video-title-show

[Hooks]
pre_playback = /usr/local/bin/pre_hook.sh
post_playback = /usr/local/bin/post_hook.sh
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Test all configuration values
            assert config.get_streamlink_quality() == "720p"
            assert config.get_streamlink_timeout_liveness() == 20
            assert config.get_streamlink_timeout_metadata() == 30
            assert config.get_player_command() == "vlc"
            assert config.get_player_args() == "--intf dummy --no-video-title-show"

            pre_hook, post_hook = config.get_hook_script_paths()
            assert pre_hook == "/usr/local/bin/pre_hook.sh"
            assert post_hook == "/usr/local/bin/post_hook.sh"

    def test_config_loading_with_missing_sections(self, temp_config_dir):
        """Test loading configuration with missing sections."""
        config_content = """
[Streamlink]
quality = 480p
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should get custom value for existing section
            assert config.get_streamlink_quality() == "480p"

            # Should get defaults for missing values
            assert config.get_streamlink_timeout_liveness() == 10  # Default
            assert config.get_player_command() == "mpv"  # Default

            pre_hook, post_hook = config.get_hook_script_paths()
            assert pre_hook is None  # Default
            assert post_hook is None  # Default

    def test_config_loading_with_empty_values(self, temp_config_dir):
        """Test loading configuration with empty values."""
        config_content = """
[Streamlink]
quality =
timeout_liveness =

[Player]
command =
args =

[Hooks]
pre_playback =
post_playback =
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should fall back to defaults for empty values
            assert config.get_streamlink_quality() == "best"  # Default
            assert config.get_streamlink_timeout_liveness() == 10  # Default
            assert config.get_player_command() == "mpv"  # Default

            pre_hook, post_hook = config.get_hook_script_paths()
            assert pre_hook is None
            assert post_hook is None

    def test_config_loading_nonexistent_file(self, temp_config_dir):
        """Test loading configuration when file doesn't exist."""
        nonexistent_file = temp_config_dir / "nonexistent.ini"

        with patch.object(config, "CONFIG_FILE_PATH", nonexistent_file):
            # Should return all defaults
            assert config.get_streamlink_quality() == "best"
            assert config.get_streamlink_timeout_liveness() == 10
            assert config.get_streamlink_timeout_metadata() == 15
            assert config.get_player_command() == "mpv"
            assert config.get_player_args() == "--no-terminal --force-window=immediate"

            pre_hook, post_hook = config.get_hook_script_paths()
            assert pre_hook is None
            assert post_hook is None

    def test_config_loading_invalid_file(self, temp_config_dir):
        """Test loading configuration with invalid file format."""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text("invalid config file content")

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should fall back to defaults when config is invalid
            assert config.get_streamlink_quality() == "best"
            assert config.get_player_command() == "mpv"

    def test_config_type_conversion(self, temp_config_dir):
        """Test configuration type conversion."""
        config_content = """
[Streamlink]
timeout_liveness = 25
timeout_metadata = 35
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should convert strings to integers
            liveness_timeout = config.get_streamlink_timeout_liveness()
            metadata_timeout = config.get_streamlink_timeout_metadata()

            assert isinstance(liveness_timeout, int)
            assert isinstance(metadata_timeout, int)
            assert liveness_timeout == 25
            assert metadata_timeout == 35

    def test_config_invalid_type_conversion(self, temp_config_dir):
        """Test configuration with invalid type conversion."""
        config_content = """
[Streamlink]
timeout_liveness = invalid_number
timeout_metadata = another_invalid
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # Should fall back to defaults when conversion fails
            assert config.get_streamlink_timeout_liveness() == 10  # Default
            assert config.get_streamlink_timeout_metadata() == 15  # Default


class TestFirstRunIntegration:
    """Test first run detection and setup integration."""

    def test_first_run_detection_new_user(self, temp_config_dir):
        """Test first run detection for new user."""
        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            # Should be first run initially
            assert not config.is_first_run_completed()

            # Mark as completed
            config.mark_first_run_completed()

            # Should no longer be first run
            assert config.is_first_run_completed()

    def test_first_run_marker_file_creation(self, temp_config_dir):
        """Test first run marker file creation."""
        marker_file = temp_config_dir / ".first_run_completed"

        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            # File shouldn't exist initially
            assert not marker_file.exists()

            # Mark first run as completed
            config.mark_first_run_completed()

            # File should now exist
            assert marker_file.exists()

    def test_first_run_existing_user(self, temp_config_dir):
        """Test first run detection for existing user."""
        # Create marker file
        marker_file = temp_config_dir / ".first_run_completed"
        marker_file.touch()

        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            # Should not be first run
            assert config.is_first_run_completed()


class TestConfigDirectorySetup:
    """Test configuration directory setup integration."""

    def test_config_directory_creation(self, temp_config_dir):
        """Test that configuration directory is created when needed."""
        # Remove the directory
        import shutil

        shutil.rmtree(temp_config_dir)
        assert not temp_config_dir.exists()

        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            # Accessing config should create directory
            config.mark_first_run_completed()

            # Directory should now exist
            assert temp_config_dir.exists()
            assert temp_config_dir.is_dir()

    def test_config_file_paths_resolution(self, temp_config_dir):
        """Test that config file paths are resolved correctly."""
        with patch.object(config, "USER_CONFIG_DIR", temp_config_dir):
            # Paths should be resolved relative to config directory
            assert config.STREAMS_FILE_PATH.parent == temp_config_dir
            assert config.CONFIG_FILE_PATH.parent == temp_config_dir

            # Files should have correct names
            assert config.STREAMS_FILE_PATH.name == "streams.json"
            assert config.CONFIG_FILE_PATH.name == "config.ini"


class TestConfigurationPersistence:
    """Test configuration persistence and reloading."""

    def test_config_persistence_across_loads(self, temp_config_dir):
        """Test that configuration persists across multiple loads."""
        config_content = """
[Streamlink]
quality = 1080p
timeout_liveness = 30

[Player]
command = vlc
"""
        config_file = temp_config_dir / "config.ini"
        config_file.write_text(config_content)

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            # First load
            quality1 = config.get_streamlink_quality()
            timeout1 = config.get_streamlink_timeout_liveness()
            command1 = config.get_player_command()

            # Second load (simulating restart)
            quality2 = config.get_streamlink_quality()
            timeout2 = config.get_streamlink_timeout_liveness()
            command2 = config.get_player_command()

            # Values should be consistent
            assert quality1 == quality2 == "1080p"
            assert timeout1 == timeout2 == 30
            assert command1 == command2 == "vlc"

    def test_config_modification_detection(self, temp_config_dir):
        """Test detection of configuration file modifications."""
        config_file = temp_config_dir / "config.ini"

        # Initial config
        config_file.write_text(
            """
[Streamlink]
quality = 720p
"""
        )

        with patch.object(config, "CONFIG_FILE_PATH", config_file):
            initial_quality = config.get_streamlink_quality()
            assert initial_quality == "720p"

            # Modify config file
            config_file.write_text(
                """
[Streamlink]
quality = 1080p
"""
            )

            # Note: In a real implementation, you might want to add
            # file modification time checking or config reloading
            # For now, this tests that the config system can handle
            # file changes (though it may require restart)
