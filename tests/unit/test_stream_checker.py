"""
Unit tests for stream checking logic module.
"""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch import stream_checker


class TestStreamLivenessChecking:
    """Test stream liveness checking functionality."""

    def test_is_stream_live_success(self, mock_subprocess_run):
        """Test successful stream liveness check."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Available streams: best, worst, 720p"
        mock_subprocess_run.return_value.stderr = ""

        result = stream_checker.is_stream_live("https://www.twitch.tv/testuser")
        assert result is True

        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert "streamlink" in call_args
        assert "https://www.twitch.tv/testuser" in call_args

    def test_is_stream_live_offline(self, mock_subprocess_run):
        """Test stream liveness check for offline stream."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = "No streams found"
        mock_subprocess_run.return_value.stderr = "Stream offline"

        result = stream_checker.is_stream_live("https://www.twitch.tv/offlineuser")
        assert result is False

    def test_is_stream_live_timeout(self, mock_subprocess_run):
        """Test stream liveness check with timeout."""
        mock_subprocess_run.side_effect = TimeoutError("Command timed out")

        result = stream_checker.is_stream_live("https://www.twitch.tv/testuser")
        assert result is False

    def test_is_stream_live_streamlink_not_found(self, mock_subprocess_run):
        """Test stream liveness check when streamlink is not found."""
        mock_subprocess_run.side_effect = FileNotFoundError("streamlink not found")

        with pytest.raises(FileNotFoundError):
            stream_checker.is_stream_live("https://www.twitch.tv/testuser")


class TestStreamMetadata:
    """Test stream metadata fetching functionality."""

    def test_get_stream_metadata_json_success(
        self, mock_subprocess_run, sample_stream_metadata
    ):
        """Test successful metadata fetching."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = json.dumps(sample_stream_metadata)
        mock_subprocess_run.return_value.stderr = ""

        success, result = stream_checker.get_stream_metadata_json(
            "https://www.twitch.tv/testuser"
        )
        assert success is True
        assert json.loads(result) == sample_stream_metadata

    def test_get_stream_metadata_json_failure(self, mock_subprocess_run):
        """Test metadata fetching failure."""
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ""
        mock_subprocess_run.return_value.stderr = "Stream not found"

        success, result = stream_checker.get_stream_metadata_json(
            "https://www.twitch.tv/testuser"
        )
        assert success is False
        assert "streamlink failed" in result

    def test_get_stream_metadata_json_timeout(self, mock_subprocess_run):
        """Test metadata fetching with timeout."""
        mock_subprocess_run.side_effect = TimeoutError("Command timed out")

        success, result = stream_checker.get_stream_metadata_json(
            "https://www.twitch.tv/testuser"
        )
        assert success is False
        assert "timeout" in result.lower()

    def test_get_stream_metadata_json_invalid_json(self, mock_subprocess_run):
        """Test metadata fetching with invalid JSON response."""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "invalid json"
        mock_subprocess_run.return_value.stderr = ""

        success, result = stream_checker.get_stream_metadata_json(
            "https://www.twitch.tv/testuser"
        )
        assert success is False
        assert "JSON processing error" in result


class TestCategoryExtraction:
    """Test category/keywords extraction functionality."""

    def test_extract_category_keywords_twitch(self):
        """Test category extraction for Twitch platform."""
        metadata_result = (
            True,
            json.dumps(
                {"metadata": {"game": "Just Chatting", "title": "Test Stream Title"}}
            ),
        )

        result = stream_checker.extract_category_keywords(metadata_result, "Twitch")
        assert result == "Just Chatting"

    def test_extract_category_keywords_youtube(self):
        """Test category extraction for YouTube platform."""
        metadata_result = (
            True,
            json.dumps(
                {
                    "metadata": {
                        "title": "Music: Live Concert Stream",
                        "category": "Music",
                    }
                }
            ),
        )

        result = stream_checker.extract_category_keywords(metadata_result, "YouTube")
        assert "Music" in result or "Live Concert Stream" in result

    def test_extract_category_keywords_no_metadata(self):
        """Test category extraction with no metadata."""
        metadata_result = (False, "Error message")

        result = stream_checker.extract_category_keywords(metadata_result, "Twitch")
        assert result == "N/A"

    def test_extract_category_keywords_invalid_json(self):
        """Test category extraction with invalid JSON."""
        metadata_result = (True, "invalid json")

        result = stream_checker.extract_category_keywords(metadata_result, "Twitch")
        assert result == "N/A"

    def test_extract_category_keywords_empty_metadata(self):
        """Test category extraction with empty metadata."""
        metadata_result = (True, json.dumps({}))

        result = stream_checker.extract_category_keywords(metadata_result, "Twitch")
        assert result == "N/A"


class TestLiveStreamsFetching:
    """Test live streams fetching functionality."""

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    def test_fetch_live_streams_all_live(
        self, mock_metadata, mock_is_live, sample_stream_data, sample_stream_metadata
    ):
        """Test fetching when all streams are live."""
        mock_is_live.return_value = True
        mock_metadata.return_value = (True, json.dumps(sample_stream_metadata))

        result = stream_checker.fetch_live_streams(sample_stream_data)

        assert len(result) == len(sample_stream_data)
        for stream in result:
            assert stream["is_live"] is True
            assert "title" in stream
            assert "category_keywords" in stream
            assert "viewer_count" in stream

    @patch("src.streamwatch.stream_checker.is_stream_live")
    def test_fetch_live_streams_none_live(self, mock_is_live, sample_stream_data):
        """Test fetching when no streams are live."""
        mock_is_live.return_value = False

        result = stream_checker.fetch_live_streams(sample_stream_data)
        assert len(result) == 0

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    def test_fetch_live_streams_mixed(
        self, mock_metadata, mock_is_live, sample_stream_data, sample_stream_metadata
    ):
        """Test fetching with mix of live and offline streams."""
        # First stream live, second offline, third live
        mock_is_live.side_effect = [True, False, True]
        mock_metadata.return_value = (True, json.dumps(sample_stream_metadata))

        result = stream_checker.fetch_live_streams(sample_stream_data)

        assert len(result) == 2  # Only live streams returned
        for stream in result:
            assert stream["is_live"] is True

    @patch("src.streamwatch.stream_checker.is_stream_live")
    def test_fetch_live_streams_streamlink_error(
        self, mock_is_live, sample_stream_data
    ):
        """Test fetching when streamlink command is not found."""
        mock_is_live.side_effect = FileNotFoundError("streamlink not found")

        with pytest.raises(FileNotFoundError):
            stream_checker.fetch_live_streams(sample_stream_data)

    @patch("src.streamwatch.stream_checker.is_stream_live")
    @patch("src.streamwatch.stream_checker.get_stream_metadata_json")
    def test_fetch_live_streams_metadata_failure(
        self, mock_metadata, mock_is_live, sample_stream_data
    ):
        """Test fetching when metadata fetching fails."""
        mock_is_live.return_value = True
        mock_metadata.side_effect = Exception("Metadata fetch failed")

        result = stream_checker.fetch_live_streams(sample_stream_data)

        # Should still return streams but with fallback metadata
        assert len(result) == len(sample_stream_data)
        for stream in result:
            assert stream["is_live"] is True
            assert "url" in stream
            assert "alias" in stream

    def test_fetch_live_streams_empty_input(self):
        """Test fetching with empty stream list."""
        result = stream_checker.fetch_live_streams([])
        assert result == []

    def test_fetch_live_streams_invalid_input(self):
        """Test fetching with invalid stream data."""
        invalid_data = [{"invalid": "data"}]  # Missing required 'url' key

        with pytest.raises(KeyError):
            stream_checker.fetch_live_streams(invalid_data)
