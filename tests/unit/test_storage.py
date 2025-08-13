"""
Unit tests for storage operations module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.streamwatch import storage


class TestStorageOperations:
    """Test storage operations for stream data."""

    def test_load_streams_empty_file(self, temp_config_dir):
        """Test loading streams when file doesn't exist."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "nonexistent.json"
            streams = storage.load_streams()
            assert streams == []

    def test_load_streams_valid_file(self, mock_streams_file, sample_stream_data):
        """Test loading streams from valid JSON file."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            streams = storage.load_streams()
            assert streams == sample_stream_data

    def test_load_streams_invalid_json(self, temp_config_dir):
        """Test loading streams from invalid JSON file."""
        invalid_file = temp_config_dir / "invalid.json"
        invalid_file.write_text("invalid json content")

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = invalid_file
            streams = storage.load_streams()
            assert streams == []

    def test_save_streams_success(self, temp_config_dir, sample_stream_data):
        """Test successfully saving streams to file."""
        streams_file = temp_config_dir / "streams.json"

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = streams_file
            mock_config.USER_CONFIG_DIR = temp_config_dir

            result = storage.save_streams(sample_stream_data)
            assert result is True

            # Verify file was created and contains correct data
            assert streams_file.exists()
            with open(streams_file) as f:
                saved_data = json.load(f)
            assert saved_data == sample_stream_data

    def test_save_streams_directory_creation(self, sample_stream_data):
        """Test that save_streams creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_dir = temp_path / "nonexistent" / "config"
            streams_file = config_dir / "streams.json"

            with patch.object(storage, "config") as mock_config:
                mock_config.STREAMS_FILE_PATH = streams_file
                mock_config.USER_CONFIG_DIR = config_dir

                result = storage.save_streams(sample_stream_data)
                assert result is True
                assert streams_file.exists()

    def test_add_streams_new_streams(self, temp_config_dir):
        """Test adding new streams to empty storage."""
        new_streams = [{"url": "https://www.twitch.tv/newuser", "alias": "New User"}]

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "streams.json"
            mock_config.USER_CONFIG_DIR = temp_config_dir

            success, message = storage.add_streams(new_streams)
            assert success is True
            assert "1 new stream(s) added" in message

    def test_add_streams_duplicates(self, mock_streams_file, sample_stream_data):
        """Test adding duplicate streams."""
        duplicate_streams = [sample_stream_data[0]]  # First stream is duplicate

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            success, message = storage.add_streams(duplicate_streams)
            assert success is False
            assert "duplicate" in message.lower()

    def test_add_streams_mixed(self, mock_streams_file):
        """Test adding mix of new and duplicate streams."""
        mixed_streams = [
            {
                "url": "https://www.twitch.tv/testuser1",
                "alias": "Duplicate",
            },  # Duplicate
            {"url": "https://www.twitch.tv/newuser", "alias": "New User"},  # New
        ]

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            success, message = storage.add_streams(mixed_streams)
            assert success is True
            assert "1 new stream(s) added" in message
            assert "1 duplicate(s) skipped" in message

    def test_remove_streams_by_indices_valid(
        self, mock_streams_file, sample_stream_data
    ):
        """Test removing streams by valid indices."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            success, message = storage.remove_streams_by_indices(
                [0, 2]
            )  # Remove first and third
            assert success is True
            assert "2 stream(s) removed" in message

            # Verify remaining streams
            remaining_streams = storage.load_streams()
            assert len(remaining_streams) == 1
            assert (
                remaining_streams[0] == sample_stream_data[1]
            )  # Only middle stream remains

    def test_remove_streams_by_indices_invalid(self, mock_streams_file):
        """Test removing streams with invalid indices."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            success, message = storage.remove_streams_by_indices([99])  # Invalid index
            assert success is False
            assert "invalid" in message.lower()

    def test_remove_streams_by_indices_empty_list(self, mock_streams_file):
        """Test removing streams with empty indices list."""
        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file
            mock_config.USER_CONFIG_DIR = mock_streams_file.parent

            success, message = storage.remove_streams_by_indices([])
            assert success is False
            assert "no indices" in message.lower()

    def test_import_streams_from_txt_valid(self, temp_config_dir):
        """Test importing streams from valid text file."""
        txt_file = temp_config_dir / "import.txt"
        txt_content = """
# Comments should be ignored
https://www.twitch.tv/user1
https://www.youtube.com/@channel1 Custom Alias

# Empty lines should be ignored

https://www.twitch.tv/user2
"""
        txt_file.write_text(txt_content)

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "streams.json"
            mock_config.USER_CONFIG_DIR = temp_config_dir

            success, message = storage.import_streams_from_txt(txt_file)
            assert success is True
            assert "imported" in message.lower()

    def test_import_streams_from_txt_nonexistent(self, temp_config_dir):
        """Test importing from nonexistent file."""
        nonexistent_file = temp_config_dir / "nonexistent.txt"

        success, message = storage.import_streams_from_txt(nonexistent_file)
        assert success is False
        assert "not found" in message.lower()

    def test_export_streams_to_json_success(
        self, mock_streams_file, sample_stream_data, temp_config_dir
    ):
        """Test successfully exporting streams to JSON."""
        export_file = temp_config_dir / "export.json"

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = mock_streams_file

            success, message = storage.export_streams_to_json(export_file)
            assert success is True
            assert "exported" in message.lower()

            # Verify exported file
            assert export_file.exists()
            with open(export_file) as f:
                exported_data = json.load(f)
            assert exported_data == sample_stream_data

    def test_export_streams_to_json_no_streams(self, temp_config_dir):
        """Test exporting when no streams exist."""
        export_file = temp_config_dir / "export.json"

        with patch.object(storage, "config") as mock_config:
            mock_config.STREAMS_FILE_PATH = temp_config_dir / "nonexistent.json"

            success, message = storage.export_streams_to_json(export_file)
            assert success is True  # Should still succeed with empty list
            assert "0 streams" in message

    def test_get_last_played_url_exists(self, temp_config_dir):
        """Test getting last played URL when file exists."""
        last_played_file = temp_config_dir / "last_played.txt"
        test_url = "https://www.twitch.tv/testuser"
        last_played_file.write_text(test_url)

        with patch.object(storage, "config") as mock_config:
            mock_config.USER_CONFIG_DIR = temp_config_dir

            url = storage.get_last_played_url()
            assert url == test_url

    def test_get_last_played_url_not_exists(self, temp_config_dir):
        """Test getting last played URL when file doesn't exist."""
        with patch.object(storage, "config") as mock_config:
            mock_config.USER_CONFIG_DIR = temp_config_dir

            url = storage.get_last_played_url()
            assert url is None

    def test_save_last_played_url(self, temp_config_dir):
        """Test saving last played URL."""
        test_url = "https://www.twitch.tv/testuser"

        with patch.object(storage, "config") as mock_config:
            mock_config.USER_CONFIG_DIR = temp_config_dir

            storage.save_last_played_url(test_url)

            # Verify file was created
            last_played_file = temp_config_dir / "last_played.txt"
            assert last_played_file.exists()
            assert last_played_file.read_text().strip() == test_url
