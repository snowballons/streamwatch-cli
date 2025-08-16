from unittest.mock import Mock, patch

import pytest

from src.streamwatch import player


class TestPlayerLaunching:
    @patch("src.streamwatch.player.subprocess.Popen")
    @patch("src.streamwatch.player.config")
    def test_launch_player_success(self, mock_config, mock_popen):
        mock_popen.return_value.poll.return_value = None
        process = player.launch_player_process("https://test.tv/user", "best")
        assert process is not None
        mock_popen.assert_called_once()
