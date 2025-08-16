"""
Sample data fixtures for testing.
"""

import json
from typing import Any, Dict, List

# Sample stream configurations
SAMPLE_STREAMS = [
    {"url": "https://www.twitch.tv/testuser1", "alias": "Test User 1"},
    {"url": "https://www.youtube.com/@testchannel", "alias": "Test Channel"},
    {"url": "https://www.twitch.tv/testuser2", "alias": "Test User 2"},
    {"url": "https://kick.com/testkicker", "alias": "Test Kicker"},
]

# Sample stream metadata responses
TWITCH_METADATA = {
    "metadata": {
        "title": "Just Chatting with Viewers",
        "author": "TestUser1",
        "game": "Just Chatting",
        "user_name": "testuser1",
        "viewers": 1234,
        "category": "IRL",
    }
}

YOUTUBE_METADATA = {
    "metadata": {
        "title": "Live Music Concert Stream",
        "author": "Test Channel",
        "category": "Music",
        "uploader": "testchannel",
        "view_count": 5678,
    }
}

# Sample live stream info (after processing)
SAMPLE_LIVE_STREAMS = [
    {
        "url": "https://www.twitch.tv/testuser1",
        "alias": "Test User 1",
        "platform": "Twitch",
        "username": "testuser1",
        "title": "Just Chatting with Viewers",
        "category_keywords": "Just Chatting",
        "viewer_count": 1234,
        "is_live": True,
    },
    {
        "url": "https://www.youtube.com/@testchannel",
        "alias": "Test Channel",
        "platform": "YouTube",
        "username": "testchannel",
        "title": "Live Music Concert Stream",
        "category_keywords": "Music",
        "viewer_count": 5678,
        "is_live": True,
    },
]

# Sample URL parsing test cases
URL_PARSING_TEST_CASES = [
    # Twitch URLs
    {
        "url": "https://www.twitch.tv/testuser",
        "expected": {
            "platform": "Twitch",
            "username": "testuser",
            "url_type": "channel",
        },
    },
    {
        "url": "https://twitch.tv/another_user",
        "expected": {
            "platform": "Twitch",
            "username": "another_user",
            "url_type": "channel",
        },
    },
    # YouTube URLs
    {
        "url": "https://www.youtube.com/@testchannel",
        "expected": {
            "platform": "YouTube",
            "username": "testchannel",
            "url_type": "channel",
        },
    },
    {
        "url": "https://youtube.com/channel/UC123456789",
        "expected": {
            "platform": "YouTube",
            "username": "UC123456789",
            "url_type": "channel",
        },
    },
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "expected": {
            "platform": "YouTube",
            "username": "unknown_user",
            "url_type": "video",
        },
    },
    # Other platforms
    {
        "url": "https://kick.com/testuser",
        "expected": {"platform": "Kick", "username": "testuser", "url_type": "channel"},
    },
    # Generic fallback
    {
        "url": "https://example.com/live/user123",
        "expected": {
            "platform": "Example",
            "username": "user123",
            "url_type": "generic_fallback",
        },
    },
    # Error cases
    {
        "url": "not a url",
        "expected": {
            "platform": "Unknown",
            "username": "unknown_stream",
            "url_type": "parse_error",
        },
    },
    {
        "url": "https://twitch.tv/",
        "expected": {
            "platform": "Twitch",
            "username": "unknown_user",
            "url_type": "parse_error",
        },
    },
]

# Sample configuration files
SAMPLE_CONFIG_FULL = """
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

SAMPLE_CONFIG_MINIMAL = """
[Streamlink]
quality = best
"""

SAMPLE_CONFIG_EMPTY_VALUES = """
[Streamlink]
quality =
timeout_liveness =

[Player]
command =
args =

[Hooks]
pre_playback =
post_playbook =
"""

# Sample streamlink command outputs
STREAMLINK_LIVE_OUTPUT = "Available streams: best, worst, 1080p, 720p, 480p, 360p, 160p"
STREAMLINK_OFFLINE_OUTPUT = "No streams found on this URL."

STREAMLINK_JSON_OUTPUT = json.dumps(
    {
        "streams": {
            "best": {"quality": "1080p"},
            "worst": {"quality": "160p"},
            "1080p": {"quality": "1080p"},
            "720p": {"quality": "720p"},
            "480p": {"quality": "480p"},
            "360p": {"quality": "360p"},
            "160p": {"quality": "160p"},
        }
    }
)

# Sample import/export files
SAMPLE_IMPORT_TXT = """
# StreamWatch Import File
# Lines starting with # are comments

https://www.twitch.tv/user1
https://www.youtube.com/@channel1 Custom Channel Name
https://kick.com/user2

# Empty lines are ignored

https://www.twitch.tv/user3 Another User
"""

SAMPLE_EXPORT_JSON = json.dumps(SAMPLE_STREAMS, indent=2)

# Error messages for testing
ERROR_MESSAGES = {
    "streamlink_not_found": "streamlink command not found",
    "stream_offline": "Stream is offline",
    "timeout": "Command timed out",
    "invalid_json": "Invalid JSON response",
    "file_not_found": "File not found",
    "permission_denied": "Permission denied",
}

# Mock process responses
MOCK_PROCESS_SUCCESS = {"returncode": 0, "stdout": STREAMLINK_LIVE_OUTPUT, "stderr": ""}

MOCK_PROCESS_FAILURE = {"returncode": 1, "stdout": "", "stderr": "Stream not found"}

MOCK_PROCESS_JSON_SUCCESS = {
    "returncode": 0,
    "stdout": json.dumps(TWITCH_METADATA),
    "stderr": "",
}


def get_sample_streams() -> List[Dict[str, str]]:
    """Get sample stream data."""
    return SAMPLE_STREAMS.copy()


def get_sample_metadata(platform: str = "twitch") -> Dict[str, Any]:
    """Get sample metadata for a platform."""
    if platform.lower() == "twitch":
        return TWITCH_METADATA.copy()
    elif platform.lower() == "youtube":
        return YOUTUBE_METADATA.copy()
    else:
        return TWITCH_METADATA.copy()


def get_sample_live_streams() -> List[Dict[str, Any]]:
    """Get sample live stream data."""
    return SAMPLE_LIVE_STREAMS.copy()


def get_url_parsing_test_cases() -> List[Dict[str, Any]]:
    """Get URL parsing test cases."""
    return URL_PARSING_TEST_CASES.copy()


def get_sample_config(config_type: str = "full") -> str:
    """Get sample configuration content."""
    configs = {
        "full": SAMPLE_CONFIG_FULL,
        "minimal": SAMPLE_CONFIG_MINIMAL,
        "empty": SAMPLE_CONFIG_EMPTY_VALUES,
    }
    return configs.get(config_type, SAMPLE_CONFIG_FULL)


def get_mock_process_response(response_type: str = "success") -> Dict[str, Any]:
    """Get mock process response."""
    responses = {
        "success": MOCK_PROCESS_SUCCESS,
        "failure": MOCK_PROCESS_FAILURE,
        "json_success": MOCK_PROCESS_JSON_SUCCESS,
    }
    return responses.get(response_type, MOCK_PROCESS_SUCCESS).copy()
