from unittest.mock import patch

import pytest

from src.streamwatch.stream_checker import _is_stream_live_core


class TestStreamLivenessChecking:
    @patch("src.streamwatch.stream_checker.subprocess.run")
    def test_is_stream_live_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Available streams: best"
        result = _is_stream_live_core("https://test.tv/user")
        assert result.is_live is True
