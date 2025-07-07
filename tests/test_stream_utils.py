# tests/test_stream_utils.py
import pytest
from streamwatch.stream_utils import parse_url_metadata

test_data = [
    # ... (all the valid platform tests from before are still good) ...
    pytest.param("https://www.twitch.tv/some_streamer", 
                 {'platform': 'Twitch', 'username': 'some_streamer', 'type': 'channel'}, id="twitch_valid"),
    # ... etc ...
    pytest.param("https://kick.com/trainwreckstv", 
                 {'platform': 'Kick', 'username': 'trainwreckstv', 'type': 'channel'}, id="kick_valid"),

    # --- Generic Fallback Test (should still work) ---
    pytest.param("https://some.random-site.com/live/user123", 
                 {'platform': 'Random-site', 'username': 'user123', 'type': 'generic_fallback'}, id="fallback_valid"),
    
    # --- Invalid/Edge Case URL Tests (THESE WILL CHANGE) ---
    pytest.param("not a url", 
                 {'platform': 'Unknown', 'username': 'unknown_stream', 'type': 'parse_error'}, id="not_a_url_string"),
    pytest.param("ftp://mysite.com/file", 
                 {'platform': 'Unknown', 'username': 'unknown_stream', 'type': 'parse_error'}, id="ftp_protocol"),
    
    # This test is now for an explicit parse error on a known platform
    pytest.param("https://twitch.tv/", 
                 {'platform': 'Twitch', 'username': 'unknown_user', 'type': 'parse_error'}, id="twitch_no_user"),

    # Add a new test for the generic fallback with no path
    pytest.param("https://someplatform.com",
                 {'platform': 'Someplatform', 'username': 'stream', 'type': 'generic_fallback'}, id="generic_no_path")
]

# The rest of the test file can remain the same
@pytest.mark.parametrize("input_url, expected_result", test_data)
def test_parse_url_metadata(input_url, expected_result):
    result = parse_url_metadata(input_url)
    assert result == expected_result