"""
Unit tests for stream utilities module.
"""
import pytest

from src.streamwatch.stream_utils import parse_url_metadata


class TestUrlParsing:
    """Test URL parsing functionality."""

    @pytest.mark.parametrize(
        "input_url, expected_result",
        [
            # Twitch URLs
            pytest.param(
                "https://www.twitch.tv/some_streamer",
                {
                    "platform": "Twitch",
                    "username": "some_streamer",
                    "url_type": "channel",
                },
                id="twitch_valid",
            ),
            pytest.param(
                "https://twitch.tv/another_user",
                {
                    "platform": "Twitch",
                    "username": "another_user",
                    "url_type": "channel",
                },
                id="twitch_no_www",
            ),
            pytest.param(
                "https://twitch.tv/",
                {
                    "platform": "Twitch",
                    "username": "unknown_user",
                    "url_type": "parse_error",
                },
                id="twitch_no_user",
            ),
            # YouTube URLs
            pytest.param(
                "https://www.youtube.com/@testchannel",
                {
                    "platform": "YouTube",
                    "username": "testchannel",
                    "url_type": "channel",
                },
                id="youtube_handle",
            ),
            pytest.param(
                "https://youtube.com/channel/UC123456789",
                {
                    "platform": "YouTube",
                    "username": "UC123456789",
                    "url_type": "channel",
                },
                id="youtube_channel_id",
            ),
            pytest.param(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                {
                    "platform": "YouTube",
                    "username": "unknown_user",
                    "url_type": "video",
                },
                id="youtube_video",
            ),
            # Other platforms
            pytest.param(
                "https://kick.com/trainwreckstv",
                {
                    "platform": "Kick",
                    "username": "trainwreckstv",
                    "url_type": "channel",
                },
                id="kick_valid",
            ),
            # Generic fallback
            pytest.param(
                "https://some.random-site.com/live/user123",
                {
                    "platform": "Random-site",
                    "username": "user123",
                    "url_type": "generic_fallback",
                },
                id="fallback_valid",
            ),
            pytest.param(
                "https://someplatform.com",
                {
                    "platform": "Someplatform",
                    "username": "stream",
                    "url_type": "generic_fallback",
                },
                id="generic_no_path",
            ),
            # Invalid URLs
            pytest.param(
                "not a url",
                {
                    "platform": "Unknown",
                    "username": "unknown_stream",
                    "url_type": "parse_error",
                },
                id="not_a_url_string",
            ),
            pytest.param(
                "ftp://mysite.com/file",
                {
                    "platform": "Unknown",
                    "username": "unknown_stream",
                    "url_type": "parse_error",
                },
                id="ftp_protocol",
            ),
        ],
    )
    def test_parse_url_metadata(self, input_url: str, expected_result: dict) -> None:
        """Test URL metadata parsing for various platforms and edge cases."""
        result = parse_url_metadata(input_url)
        assert result == expected_result

    def test_parse_url_metadata_empty_string(self):
        """Test parsing empty string URL."""
        result = parse_url_metadata("")
        assert result["platform"] == "Unknown"
        assert result["url_type"] == "parse_error"

    def test_parse_url_metadata_none_input(self):
        """Test parsing None input."""
        with pytest.raises(AttributeError):
            parse_url_metadata(None)

    def test_parse_url_metadata_case_insensitive(self):
        """Test that URL parsing is case insensitive for domains."""
        result1 = parse_url_metadata("https://TWITCH.TV/testuser")
        result2 = parse_url_metadata("https://twitch.tv/testuser")

        assert result1["platform"] == result2["platform"]
        assert result1["username"] == result2["username"]

    def test_parse_url_metadata_with_query_params(self):
        """Test URL parsing with query parameters."""
        result = parse_url_metadata("https://www.twitch.tv/testuser?param=value")
        assert result["platform"] == "Twitch"
        assert result["username"] == "testuser"
        assert result["url_type"] == "channel"

    def test_parse_url_metadata_with_fragments(self):
        """Test URL parsing with URL fragments."""
        result = parse_url_metadata("https://www.twitch.tv/testuser#section")
        assert result["platform"] == "Twitch"
        assert result["username"] == "testuser"
        assert result["url_type"] == "channel"
