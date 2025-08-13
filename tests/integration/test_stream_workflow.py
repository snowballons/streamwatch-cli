"""
Integration tests for end-to-end stream workflows.
"""
import json
from unittest.mock import Mock, patch

import pytest

from src.streamwatch import core, player, storage, stream_checker


class TestStreamManagementWorkflow:
    """Test complete stream management workflows."""

    def test_add_and_load_streams_workflow(self, temp_config_dir):
        """Test adding streams and loading them back."""
        # Add streams
        new_streams = [
            {"url": "https://www.twitch.tv/testuser1", "alias": "Test User 1"},
            {"url": "https://www.youtube.com/@testchannel", "alias": "Test Channel"},
        ]

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "streams.json"
            mock_config.USER_CONFIG_DIR = temp_config_dir

            # Add streams
            success, message = storage.add_streams(new_streams)
            assert success is True

            # Load streams back
            loaded_streams = storage.load_streams()
            assert len(loaded_streams) == 2
            assert loaded_streams == new_streams

    def test_remove_streams_workflow(self, mock_streams_file, sample_stream_data):
        """Test removing streams workflow."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            # Load initial streams
            initial_streams = storage.load_streams()
            assert len(initial_streams) == 3

            # Remove first stream
            success, message = storage.remove_streams_by_indices([0])
            assert success is True

            # Verify removal
            remaining_streams = storage.load_streams()
            assert len(remaining_streams) == 2
            assert remaining_streams[0] == sample_stream_data[1]

    def test_import_export_workflow(self, temp_config_dir, sample_stream_data):
        """Test import and export workflow."""
        # Create initial streams
        streams_file = temp_config_dir / "streams.json"
        with open(streams_file, "w") as f:
            json.dump(sample_stream_data, f)

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = streams_file

            # Export streams
            export_file = temp_config_dir / "exported.json"
            success, message = storage.export_streams_to_json(export_file)
            assert success is True
            assert export_file.exists()

            # Verify exported content
            with open(export_file) as f:
                exported_data = json.load(f)
            assert exported_data == sample_stream_data


class TestStreamCheckingWorkflow:
    """Test stream checking and metadata workflows."""

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    def test_live_stream_detection_workflow(
        self, mock_metadata, mock_is_live, sample_stream_data, sample_stream_metadata
    ):
        """Test complete live stream detection workflow."""
        # Mock stream liveness
        mock_is_live.side_effect = [True, False, True]  # First and third are live
        mock_metadata.return_value = (True, json.dumps(sample_stream_metadata))

        # Fetch live streams
        live_streams = stream_checker.fetch_live_streams(sample_stream_data)

        # Verify results
        assert len(live_streams) == 2  # Only live streams
        for stream in live_streams:
            assert stream["is_live"] is True
            assert "title" in stream
            assert "category_keywords" in stream
            assert "viewer_count" in stream
            assert stream["url"] in [
                sample_stream_data[0]["url"],
                sample_stream_data[2]["url"],
            ]

    @patch("src.streamwatch.stream_checker.is_stream_live")
    def test_no_live_streams_workflow(self, mock_is_live, sample_stream_data):
        """Test workflow when no streams are live."""
        mock_is_live.return_value = False

        live_streams = stream_checker.fetch_live_streams(sample_stream_data)
        assert len(live_streams) == 0

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    def test_metadata_extraction_workflow(self, mock_metadata, mock_is_live):
        """Test metadata extraction workflow for different platforms."""
        mock_is_live.return_value = True

        # Test Twitch metadata
        twitch_metadata = {
            "metadata": {
                "game": "Just Chatting",
                "title": "Test Twitch Stream",
                "user_name": "testuser",
                "viewers": 1234,
            }
        }
        mock_metadata.return_value = (True, json.dumps(twitch_metadata))

        twitch_streams = [
            {"url": "https://www.twitch.tv/testuser", "alias": "Test User"}
        ]
        result = stream_checker.fetch_live_streams(twitch_streams)

        assert len(result) == 1
        assert result[0]["category_keywords"] == "Just Chatting"
        assert result[0]["viewer_count"] == 1234
        assert result[0]["username"] == "testuser"


class TestPlayerWorkflow:
    """Test player launching and management workflows."""

    @patch("src.streamwatch.player.subprocess.Popen")
    def test_player_launch_workflow(self, mock_popen):
        """Test complete player launch workflow."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        with patch(
            "src.streamwatch.player.config.get_player_command"
        ) as mock_get_command:
            mock_get_command.return_value = "mpv"

            # Launch player
            process = player.launch_player("https://www.twitch.tv/testuser", "720p")

            assert process is not None
            assert process == mock_process

            # Verify command construction
            call_args = mock_popen.call_args[0][0]
            assert "streamlink" in call_args
            assert "https://www.twitch.tv/testuser" in call_args
            assert "720p" in call_args

    @patch("src.streamwatch.player.subprocess.run")
    def test_quality_fetching_workflow(self, mock_run):
        """Test quality fetching workflow."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(
            {
                "streams": {
                    "best": {"quality": "1080p"},
                    "720p": {"quality": "720p"},
                    "480p": {"quality": "480p"},
                    "worst": {"quality": "160p"},
                }
            }
        )

        qualities = player.fetch_available_qualities("https://www.twitch.tv/testuser")

        assert qualities is not None
        assert len(qualities) >= 4
        assert "best" in qualities
        assert "720p" in qualities

    def test_player_termination_workflow(self):
        """Test player termination workflow."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = 0

        # Terminate player
        player.terminate_player_process(mock_process)

        # Verify termination sequence
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    @patch("src.streamwatch.player.subprocess.Popen")
    def test_complete_stream_playback_workflow(
        self,
        mock_popen,
        mock_metadata,
        mock_is_live,
        temp_config_dir,
        sample_stream_data,
        sample_stream_metadata,
    ):
        """Test complete workflow from stream detection to playback."""
        # Setup mocks
        mock_is_live.return_value = True
        mock_metadata.return_value = (True, json.dumps(sample_stream_metadata))

        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Setup storage
        streams_file = temp_config_dir / "streams.json"
        with open(streams_file, "w") as f:
            json.dump(sample_stream_data, f)

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = streams_file

            # Load streams
            streams = storage.load_streams()
            assert len(streams) == 3

            # Check for live streams
            live_streams = stream_checker.fetch_live_streams(streams)
            assert len(live_streams) == 3  # All mocked as live

            # Launch player for first live stream
            with patch(
                "src.streamwatch.player.config.get_player_command"
            ) as mock_get_command:
                mock_get_command.return_value = "mpv"

                process = player.launch_player(live_streams[0]["url"], "720p")
                assert process is not None

                # Terminate player
                player.terminate_player_process(process)

    @patch("src.streamwatch.stream_checker.is_stream_live")
    def test_no_live_streams_workflow(
        self, mock_is_live, temp_config_dir, sample_stream_data
    ):
        """Test workflow when no streams are live."""
        mock_is_live.return_value = False

        # Setup storage
        streams_file = temp_config_dir / "streams.json"
        with open(streams_file, "w") as f:
            json.dump(sample_stream_data, f)

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = streams_file

            # Load streams
            streams = storage.load_streams()
            assert len(streams) == 3

            # Check for live streams
            live_streams = stream_checker.fetch_live_streams(streams)
            assert len(live_streams) == 0  # None are live

    def test_error_handling_workflow(self, temp_config_dir):
        """Test error handling in workflows."""
        # Test with non-existent streams file
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "nonexistent.json"

            # Should return empty list, not crash
            streams = storage.load_streams()
            assert streams == []

            # Should handle empty stream list gracefully
            live_streams = stream_checker.fetch_live_streams(streams)
            assert live_streams == []
