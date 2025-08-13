"""Tests for the StreamManager class."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch.stream_manager import StreamManager


class TestStreamManager:
    """Test StreamManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stream_manager = StreamManager()

    def test_init(self):
        """Test StreamManager initialization."""
        assert isinstance(self.stream_manager, StreamManager)

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_add_streams_success(self, mock_storage, mock_ui):
        """Test successful stream addition."""
        mock_ui.prompt_add_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_storage.add_streams.return_value = (True, "Success message")

        success, message = self.stream_manager.add_streams()

        assert success is True
        assert message == "Success message"
        mock_ui.prompt_add_streams.assert_called_once()
        mock_storage.add_streams.assert_called_once()

    @patch("src.streamwatch.stream_manager.ui")
    def test_add_streams_cancelled(self, mock_ui):
        """Test cancelled stream addition."""
        mock_ui.prompt_add_streams.return_value = []

        success, message = self.stream_manager.add_streams()

        assert success is False
        assert "cancelled" in message
        mock_ui.prompt_add_streams.assert_called_once()

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_remove_streams_success(self, mock_storage, mock_ui):
        """Test successful stream removal."""
        mock_storage.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_ui.prompt_remove_streams_dialog.return_value = [0]
        mock_storage.remove_streams_by_indices.return_value = (
            True,
            "Removed successfully",
        )

        success, message = self.stream_manager.remove_streams()

        assert success is True
        assert message == "Removed successfully"
        mock_storage.load_streams.assert_called_once()
        mock_ui.prompt_remove_streams_dialog.assert_called_once()
        mock_storage.remove_streams_by_indices.assert_called_with([0])

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_remove_streams_cancelled(self, mock_storage, mock_ui):
        """Test cancelled stream removal."""
        mock_storage.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_ui.prompt_remove_streams_dialog.return_value = None  # Cancelled

        success, message = self.stream_manager.remove_streams()

        assert success is False
        assert "cancelled" in message

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_remove_streams_empty_selection(self, mock_storage, mock_ui):
        """Test empty stream removal selection."""
        mock_storage.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_ui.prompt_remove_streams_dialog.return_value = []  # Empty list

        success, message = self.stream_manager.remove_streams()

        assert success is False
        assert "No valid streams selected" in message

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_list_streams(self, mock_storage, mock_ui):
        """Test listing streams."""
        test_streams = [{"url": "test_url", "alias": "test_alias"}]
        mock_storage.load_streams.return_value = test_streams

        self.stream_manager.list_streams()

        mock_ui.clear_screen.assert_called_once()
        mock_storage.load_streams.assert_called_once()
        mock_ui.display_stream_list.assert_called_with(
            test_streams, title="--- All Configured Streams ---"
        )
        mock_ui.show_message.assert_called_with("", duration=0, pause_after=True)

    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_import_streams_success(self, mock_storage, mock_ui):
        """Test successful stream import."""
        mock_ui.prompt_for_filepath.return_value = "/path/to/file.txt"
        mock_storage.import_streams_from_txt.return_value = (True, "Import successful")

        success, message = self.stream_manager.import_streams()

        assert success is True
        assert message == "Import successful"
        mock_ui.prompt_for_filepath.assert_called_once()
        mock_storage.import_streams_from_txt.assert_called_with(
            Path("/path/to/file.txt")
        )

    @patch("src.streamwatch.stream_manager.ui")
    def test_import_streams_cancelled(self, mock_ui):
        """Test cancelled stream import."""
        mock_ui.prompt_for_filepath.return_value = None

        success, message = self.stream_manager.import_streams()

        assert success is False
        assert message == "Import cancelled."

    @patch("src.streamwatch.stream_manager.time")
    @patch("src.streamwatch.stream_manager.ui")
    @patch("src.streamwatch.stream_manager.storage")
    def test_export_streams_success(self, mock_storage, mock_ui, mock_time):
        """Test successful stream export."""
        mock_time.strftime.return_value = "2023-01-01"
        mock_ui.prompt_for_filepath.return_value = "/path/to/export.json"
        mock_storage.export_streams_to_json.return_value = (True, "Export successful")

        success, message = self.stream_manager.export_streams()

        assert success is True
        assert message == "Export successful"
        mock_ui.prompt_for_filepath.assert_called_once()
        mock_storage.export_streams_to_json.assert_called_with(
            Path("/path/to/export.json")
        )

    @patch("src.streamwatch.stream_manager.time")
    @patch("src.streamwatch.stream_manager.ui")
    def test_export_streams_cancelled(self, mock_ui, mock_time):
        """Test cancelled stream export."""
        mock_time.strftime.return_value = "2023-01-01"
        mock_ui.prompt_for_filepath.return_value = None

        success, message = self.stream_manager.export_streams()

        assert success is False
        assert message == "Export cancelled."

    @patch("src.streamwatch.stream_manager.storage")
    def test_load_streams(self, mock_storage):
        """Test loading streams."""
        test_streams = [{"url": "test_url", "alias": "test_alias"}]
        mock_storage.load_streams.return_value = test_streams

        result = self.stream_manager.load_streams()

        assert result == test_streams
        mock_storage.load_streams.assert_called_once()

    @patch("src.streamwatch.stream_manager.storage")
    def test_get_stream_count(self, mock_storage):
        """Test getting stream count."""
        test_streams = [{"url": "test1"}, {"url": "test2"}, {"url": "test3"}]
        mock_storage.load_streams.return_value = test_streams

        count = self.stream_manager.get_stream_count()

        assert count == 3
        mock_storage.load_streams.assert_called_once()

    @patch("src.streamwatch.stream_manager.storage")
    def test_get_stream_count_empty(self, mock_storage):
        """Test getting stream count when no streams exist."""
        mock_storage.load_streams.return_value = []

        count = self.stream_manager.get_stream_count()

        assert count == 0
