"""
Common test fixtures and configuration for StreamWatch CLI tests.
"""
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files during tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_stream_data() -> List[Dict[str, str]]:
    """Sample stream data for testing."""
    return [
        {"url": "https://www.twitch.tv/testuser1", "alias": "Test User 1"},
        {"url": "https://www.youtube.com/@testchannel", "alias": "Test Channel"},
        {"url": "https://www.twitch.tv/testuser2", "alias": "Test User 2"},
    ]


@pytest.fixture
def sample_stream_metadata() -> Dict[str, Any]:
    """Sample stream metadata for testing."""
    return {
        "metadata": {
            "title": "Test Stream Title",
            "author": "Test Author",
            "game": "Test Game",
            "viewers": 1234,
            "user_name": "testuser",
            "category": "Gaming",
        }
    }


@pytest.fixture
def mock_streamlink_process():
    """Mock subprocess for streamlink commands."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = "Available streams: best, worst, 720p, 480p"
    mock_process.stderr = ""
    return mock_process


@pytest.fixture
def mock_config_file(temp_config_dir):
    """Create a mock config file for testing."""
    config_content = """
[Streamlink]
quality = best
timeout_liveness = 10
timeout_metadata = 15

[Player]
command = mpv
args = --no-terminal --force-window=immediate

[Hooks]
pre_playback =
post_playback =
"""
    config_file = temp_config_dir / "config.ini"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_streams_file(temp_config_dir, sample_stream_data):
    """Create a mock streams.json file for testing."""
    streams_file = temp_config_dir / "streams.json"
    with open(streams_file, "w") as f:
        json.dump(sample_stream_data, f, indent=2)
    return streams_file


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing external commands."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_popen():
    """Mock subprocess.Popen for testing background processes."""
    with patch("subprocess.Popen") as mock_popen:
        yield mock_popen


@pytest.fixture
def sample_url_metadata() -> List[Dict[str, str]]:
    """Sample URL metadata for testing URL parsing."""
    return [
        {
            "url": "https://www.twitch.tv/testuser",
            "platform": "Twitch",
            "username": "testuser",
            "url_type": "channel",
        },
        {
            "url": "https://www.youtube.com/@testchannel",
            "platform": "YouTube",
            "username": "testchannel",
            "url_type": "channel",
        },
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "platform": "YouTube",
            "username": "unknown_user",
            "url_type": "video",
        },
    ]


@pytest.fixture
def mock_live_stream_info() -> List[Dict[str, Any]]:
    """Sample live stream info for testing."""
    return [
        {
            "url": "https://www.twitch.tv/testuser1",
            "alias": "Test User 1",
            "platform": "Twitch",
            "username": "testuser1",
            "title": "Test Stream 1",
            "category_keywords": "Gaming",
            "viewer_count": 1234,
            "is_live": True,
        },
        {
            "url": "https://www.youtube.com/@testchannel",
            "alias": "Test Channel",
            "platform": "YouTube",
            "username": "testchannel",
            "title": "Test Stream 2",
            "category_keywords": "Music",
            "viewer_count": 5678,
            "is_live": True,
        },
    ]


@pytest.fixture(autouse=True)
def mock_user_config_dir(temp_config_dir, monkeypatch):
    """Automatically mock the user config directory for all tests."""
    monkeypatch.setattr("src.streamwatch.config.USER_CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr(
        "src.streamwatch.config.STREAMS_FILE_PATH", temp_config_dir / "streams.json"
    )
    monkeypatch.setattr(
        "src.streamwatch.config.CONFIG_FILE_PATH", temp_config_dir / "config.ini"
    )
