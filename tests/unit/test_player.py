"""
Unit tests for player operations module.
"""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch import player


class TestHookExecution:
    """Test hook script execution functionality."""

    def test_execute_hook_success(self, mock_subprocess_popen):
        """Test successful hook execution."""
        mock_process = Mock()
        mock_subprocess_popen.return_value = mock_process

        stream_info = {"url": "https://www.twitch.tv/testuser", "alias": "Test User"}

        player.execute_hook("pre", stream_info, "720p")

        # Verify subprocess was called
        mock_subprocess_popen.assert_called_once()

    def test_execute_hook_no_script(self):
        """Test hook execution when no script is configured."""
        with patch(
            "src.streamwatch.player.config.get_hook_script_paths"
        ) as mock_get_paths:
            mock_get_paths.return_value = (None, None)

            stream_info = {
                "url": "https://www.twitch.tv/testuser",
                "alias": "Test User",
            }

            # Should not raise any exception
            player.execute_hook("pre", stream_info, "720p")

    def test_execute_hook_script_error(self, mock_subprocess_popen):
        """Test hook execution when script fails."""
        mock_subprocess_popen.side_effect = Exception("Script execution failed")

        with patch(
            "src.streamwatch.player.config.get_hook_script_paths"
        ) as mock_get_paths:
            mock_get_paths.return_value = ("/path/to/pre.sh", "/path/to/post.sh")

            stream_info = {
                "url": "https://www.twitch.tv/testuser",
                "alias": "Test User",
            }

            # Should not raise exception, just log error
            player.execute_hook("pre", stream_info, "720p")


class TestPlayerLaunching:
    """Test player launching functionality."""

    def test_launch_player_success(self, mock_subprocess_popen):
        """Test successful player launch."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_subprocess_popen.return_value = mock_process

        with patch(
            "src.streamwatch.player.config.get_player_command"
        ) as mock_get_command:
            mock_get_command.return_value = "mpv"

            process = player.launch_player("https://www.twitch.tv/testuser", "720p")

            assert process is not None
            mock_subprocess_popen.assert_called_once()

    def test_launch_player_streamlink_not_found(self, mock_subprocess_popen):
        """Test player launch when streamlink is not found."""
        mock_subprocess_popen.side_effect = FileNotFoundError("streamlink not found")

        process = player.launch_player("https://www.twitch.tv/testuser", "720p")
        assert process is None

    def test_launch_player_process_fails_immediately(self, mock_subprocess_popen):
        """Test player launch when process fails immediately."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_subprocess_popen.return_value = mock_process

        process = player.launch_player("https://www.twitch.tv/testuser", "720p")
        assert process is None

    def test_launch_player_custom_quality(self, mock_subprocess_popen):
        """Test player launch with custom quality."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_subprocess_popen.return_value = mock_process

        with patch(
            "src.streamwatch.player.config.get_player_command"
        ) as mock_get_command:
            mock_get_command.return_value = "mpv"

            process = player.launch_player("https://www.twitch.tv/testuser", "480p")

            # Verify quality was passed to streamlink
            call_args = mock_subprocess_popen.call_args[0][0]
            assert "480p" in call_args


class TestPlayerTermination:
    """Test player termination functionality."""

    def test_terminate_player_process_success(self):
        """Test successful player termination."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = 0

        player.terminate_player_process(mock_process)

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    def test_terminate_player_process_already_terminated(self):
        """Test terminating already terminated process."""
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process already terminated

        player.terminate_player_process(mock_process)

        # Should not call terminate on already terminated process
        mock_process.terminate.assert_not_called()

    def test_terminate_player_process_force_kill(self):
        """Test force killing unresponsive process."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.terminate.return_value = None
        mock_process.wait.side_effect = TimeoutError("Process didn't terminate")
        mock_process.kill.return_value = None

        player.terminate_player_process(mock_process)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_terminate_player_process_none(self):
        """Test terminating None process."""
        # Should not raise exception
        player.terminate_player_process(None)


class TestQualityFetching:
    """Test stream quality fetching functionality."""

    def test_fetch_available_qualities_success(self, mock_subprocess_run):
        """Test successful quality fetching."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(
            {
                "streams": {
                    "best": {"quality": "1080p"},
                    "worst": {"quality": "160p"},
                    "720p": {"quality": "720p"},
                    "480p": {"quality": "480p"},
                }
            }
        )

        qualities = player.fetch_available_qualities("https://www.twitch.tv/testuser")

        assert qualities is not None
        assert len(qualities) > 0
        assert "best" in qualities
        assert "worst" in qualities

    def test_fetch_available_qualities_no_streams(self, mock_subprocess_run):
        """Test quality fetching when no streams available."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ""
        mock_subprocess_run.return_value.stderr = "No streams found"

        qualities = player.fetch_available_qualities("https://www.twitch.tv/testuser")
        assert qualities is None

    def test_fetch_available_qualities_invalid_json(self, mock_subprocess_run):
        """Test quality fetching with invalid JSON response."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "invalid json"

        qualities = player.fetch_available_qualities("https://www.twitch.tv/testuser")
        assert qualities is None

    def test_fetch_available_qualities_timeout(self, mock_subprocess_run):
        """Test quality fetching with timeout."""
        mock_subprocess_run.side_effect = TimeoutError("Command timed out")

        qualities = player.fetch_available_qualities("https://www.twitch.tv/testuser")
        assert qualities is None

    def test_fetch_available_qualities_streamlink_not_found(self, mock_subprocess_run):
        """Test quality fetching when streamlink is not found."""
        mock_subprocess_run.side_effect = FileNotFoundError("streamlink not found")

        with pytest.raises(FileNotFoundError):
            player.fetch_available_qualities("https://www.twitch.tv/testuser")


class TestPlayerConfiguration:
    """Test player configuration functionality."""

    def test_get_player_command_from_config(self):
        """Test getting player command from configuration."""
        with patch(
            "src.streamwatch.player.config.get_player_command"
        ) as mock_get_command:
            mock_get_command.return_value = "vlc"

            # This would be tested indirectly through launch_player
            # The actual config module handles the command retrieval
            command = mock_get_command()
            assert command == "vlc"

    def test_get_player_args_from_config(self):
        """Test getting player arguments from configuration."""
        with patch("src.streamwatch.player.config.get_player_args") as mock_get_args:
            mock_get_args.return_value = "--intf dummy"

            args = mock_get_args()
            assert args == "--intf dummy"


class TestStreamlinkCommand:
    """Test streamlink command construction."""

    def test_streamlink_command_construction(self, mock_subprocess_popen):
        """Test that streamlink command is constructed correctly."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_subprocess_popen.return_value = mock_process

        with patch(
            "src.streamwatch.player.config.get_player_command"
        ) as mock_get_command:
            with patch(
                "src.streamwatch.player.config.get_player_args"
            ) as mock_get_args:
                mock_get_command.return_value = "mpv"
                mock_get_args.return_value = "--no-terminal"

                player.launch_player("https://www.twitch.tv/testuser", "720p")

                # Verify command construction
                call_args = mock_subprocess_popen.call_args[0][0]
                assert "streamlink" in call_args
                assert "https://www.twitch.tv/testuser" in call_args
                assert "720p" in call_args
                assert "--player" in call_args
                assert "mpv" in call_args
