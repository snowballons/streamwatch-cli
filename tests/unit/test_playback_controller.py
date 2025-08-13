"""Tests for the PlaybackController class."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch.playback_controller import PlaybackController


class TestPlaybackController:
    """Test PlaybackController functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.playback_controller = PlaybackController()

    def test_init(self):
        """Test PlaybackController initialization."""
        assert isinstance(self.playback_controller, PlaybackController)

    @patch("src.streamwatch.playback_controller.player")
    @patch("src.streamwatch.playback_controller.ui")
    def test_start_playback_session_stream_not_in_list(self, mock_ui, mock_player):
        """Test playback session when stream is not in live list."""
        initial_stream_info = {"url": "test_url", "username": "test_user"}
        all_live_streams = [{"url": "other_url", "username": "other_user"}]

        result = self.playback_controller.start_playback_session(
            initial_stream_info, "best", all_live_streams
        )

        assert result == "return_to_main"
        mock_ui.console.print.assert_called()

    @patch("src.streamwatch.playback_controller.config")
    @patch("src.streamwatch.playback_controller.player")
    @patch("src.streamwatch.playback_controller.ui")
    def test_start_playback_session_launch_failure(
        self, mock_ui, mock_player, mock_config
    ):
        """Test playback session when player launch fails."""
        initial_stream_info = {"url": "test_url", "username": "test_user"}
        all_live_streams = [{"url": "test_url", "username": "test_user"}]

        mock_player.launch_player_process.return_value = None  # Launch failure

        result = self.playback_controller.start_playback_session(
            initial_stream_info, "best", all_live_streams
        )

        assert result == "return_to_main"
        mock_player.execute_hook.assert_called()
        mock_ui.show_message.assert_called()

    def test_handle_playback_controls_next(self):
        """Test handling next stream control."""
        current_stream_info = {"url": "test_url", "username": "test_user"}
        all_live_streams = [
            {"url": "test_url", "username": "test_user"},
            {"url": "next_url", "username": "next_user"},
        ]

        with patch("src.streamwatch.playback_controller.player") as mock_player, patch(
            "src.streamwatch.playback_controller.config"
        ) as mock_config:
            mock_config.get_streamlink_quality.return_value = "best"
            mock_player_process = Mock()

            result = self.playback_controller.handle_playback_controls(
                "next",
                None,
                current_stream_info,
                "best",
                all_live_streams,
                0,
                True,
                mock_player_process,
            )

            assert result["new_index"] == 1
            assert result["new_stream_info"]["url"] == "next_url"
            assert result["user_intent_direction"] == 1
            mock_player.terminate_player_process.assert_called_with(mock_player_process)

    def test_handle_playback_controls_previous(self):
        """Test handling previous stream control."""
        current_stream_info = {"url": "test_url", "username": "test_user"}
        all_live_streams = [
            {"url": "prev_url", "username": "prev_user"},
            {"url": "test_url", "username": "test_user"},
        ]

        with patch("src.streamwatch.playback_controller.player") as mock_player, patch(
            "src.streamwatch.playback_controller.config"
        ) as mock_config:
            mock_config.get_streamlink_quality.return_value = "best"
            mock_player_process = Mock()

            result = self.playback_controller.handle_playback_controls(
                "previous",
                None,
                current_stream_info,
                "best",
                all_live_streams,
                1,
                True,
                mock_player_process,
            )

            assert result["new_index"] == 0
            assert result["new_stream_info"]["url"] == "prev_url"
            assert result["user_intent_direction"] == -1

    def test_handle_playback_controls_stop(self):
        """Test handling stop control."""
        result = self.playback_controller.handle_playback_controls(
            "stop", None, {}, "best", [], 0, True, None
        )

        assert result["terminate"] is True
        assert result["return_action"] == "stop_playback"

    @patch("src.streamwatch.playback_controller.ui")
    def test_handle_playback_controls_main_menu(self, mock_ui):
        """Test handling main menu control."""
        result = self.playback_controller.handle_playback_controls(
            "main_menu", None, {}, "best", [], 0, True, None
        )

        assert result["terminate"] is True
        assert result["return_action"] == "return_to_main"
        mock_ui.console.print.assert_called()

    @patch("src.streamwatch.playback_controller.ui")
    @patch("src.streamwatch.playback_controller.player")
    def test_handle_playback_controls_change_quality(self, mock_player, mock_ui):
        """Test handling quality change control."""
        current_stream_info = {"url": "test_url", "username": "test_user"}
        mock_player.fetch_available_qualities.return_value = ["best", "720p", "480p"]
        mock_ui.select_quality_dialog.return_value = "720p"
        mock_player_process = Mock()

        result = self.playback_controller.handle_playback_controls(
            "change_quality",
            None,
            current_stream_info,
            "best",
            [],
            0,
            True,
            mock_player_process,
        )

        assert result["new_quality"] == "720p"
        assert result["user_intent_direction"] == 0
        mock_player.terminate_player_process.assert_called_with(mock_player_process)
        mock_ui.select_quality_dialog.assert_called()

    @patch("src.streamwatch.playback_controller.webbrowser")
    @patch("src.streamwatch.playback_controller.config")
    @patch("src.streamwatch.playback_controller.ui")
    def test_handle_playback_controls_donate(
        self, mock_ui, mock_config, mock_webbrowser
    ):
        """Test handling donate control."""
        mock_config.get_donation_link.return_value = "https://donate.example.com"

        result = self.playback_controller.handle_playback_controls(
            "donate", None, {}, "best", [], 0, True, None
        )

        assert result["terminate"] is False
        mock_webbrowser.open.assert_called_with("https://donate.example.com")
        mock_ui.console.print.assert_called()

    def test_handle_playback_controls_quit(self):
        """Test handling quit control."""
        result = self.playback_controller.handle_playback_controls(
            "quit", None, {}, "best", [], 0, True, None
        )

        assert result["terminate"] is True
        assert result["return_action"] == "quit_application"

    @patch("src.streamwatch.playback_controller.ui")
    def test_handle_playback_controls_next_not_possible(self, mock_ui):
        """Test handling next when navigation is not possible."""
        result = self.playback_controller.handle_playback_controls(
            "next", None, {}, "best", [], 0, False, None
        )

        assert result["terminate"] is False
        mock_ui.console.print.assert_called_with(
            "No next stream available.", style="warning"
        )

    @patch("src.streamwatch.playback_controller.ui")
    def test_handle_playback_controls_previous_not_possible(self, mock_ui):
        """Test handling previous when navigation is not possible."""
        result = self.playback_controller.handle_playback_controls(
            "previous", None, {}, "best", [], 0, False, None
        )

        assert result["terminate"] is False
        mock_ui.console.print.assert_called_with(
            "No previous stream available.", style="warning"
        )

    @patch("src.streamwatch.playback_controller.player")
    def test_stop_playback(self, mock_player):
        """Test stopping playback."""
        mock_player_process = Mock()
        stream_info = {"url": "test_url", "username": "test_user"}
        quality = "best"

        self.playback_controller.stop_playback(
            mock_player_process, stream_info, quality
        )

        mock_player.terminate_player_process.assert_called_with(mock_player_process)
        mock_player.execute_hook.assert_called_with("post", stream_info, quality)

    def test_handle_playback_controls_unknown_action(self):
        """Test handling unknown control action."""
        result = self.playback_controller.handle_playback_controls(
            "unknown", None, {}, "best", [], 0, True, None
        )

        assert result["terminate"] is False
        assert result["return_action"] is None
