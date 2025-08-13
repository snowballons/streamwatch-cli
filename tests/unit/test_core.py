"""Tests for the refactored core module."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch.core import (
    _refresh_live_streams,
    _show_first_time_welcome,
    run_interactive_loop,
    run_playback_session,
)


class TestCore:
    """Test core module functionality."""

    @patch("src.streamwatch.core.PlaybackController")
    def test_run_playback_session_wrapper(self, mock_playback_controller_class):
        """Test that run_playback_session is a proper wrapper."""
        mock_controller = Mock()
        mock_playback_controller_class.return_value = mock_controller
        mock_controller.start_playback_session.return_value = "stop_playback"

        initial_stream_info = {"url": "test_url", "username": "test_user"}
        initial_quality = "best"
        all_live_streams = [initial_stream_info]

        result = run_playback_session(
            initial_stream_info, initial_quality, all_live_streams
        )

        assert result == "stop_playback"
        mock_playback_controller_class.assert_called_once()
        mock_controller.start_playback_session.assert_called_once_with(
            initial_stream_info, initial_quality, all_live_streams
        )

    @patch("src.streamwatch.core.ui")
    def test_show_first_time_welcome(self, mock_ui):
        """Test first-time welcome message display."""
        _show_first_time_welcome()

        mock_ui.clear_screen.assert_called_once()
        mock_ui.console.print.assert_called()
        mock_ui.show_message.assert_called_with("", duration=0, pause_after=True)

    @patch("src.streamwatch.core.stream_checker")
    @patch("src.streamwatch.core.ui")
    def test_refresh_live_streams_success(self, mock_ui, mock_stream_checker):
        """Test successful live streams refresh."""
        mock_stream_manager = Mock()
        mock_stream_manager.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_stream_checker.fetch_live_streams.return_value = [
            {"url": "test_url", "username": "test_user"}
        ]

        result = _refresh_live_streams(mock_stream_manager)

        assert len(result) == 1
        assert result[0]["url"] == "test_url"
        mock_ui.clear_screen.assert_called_once()
        mock_stream_manager.load_streams.assert_called_once()
        mock_stream_checker.fetch_live_streams.assert_called_once()

    @patch("src.streamwatch.core.stream_checker")
    @patch("src.streamwatch.core.ui")
    def test_refresh_live_streams_no_streams(self, mock_ui, mock_stream_checker):
        """Test refresh when no streams are configured."""
        mock_stream_manager = Mock()
        mock_stream_manager.load_streams.return_value = []

        result = _refresh_live_streams(mock_stream_manager)

        assert result == []
        mock_ui.console.print.assert_called()
        mock_stream_checker.fetch_live_streams.assert_not_called()

    @patch("src.streamwatch.core.stream_checker")
    @patch("src.streamwatch.core.ui")
    def test_refresh_live_streams_streamlink_error(self, mock_ui, mock_stream_checker):
        """Test refresh when streamlink is not found."""
        mock_stream_manager = Mock()
        mock_stream_manager.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_stream_checker.fetch_live_streams.side_effect = FileNotFoundError(
            "streamlink not found"
        )

        with pytest.raises(SystemExit) as exc_info:
            _refresh_live_streams(mock_stream_manager)

        assert exc_info.value.code == 1
        mock_ui.show_message.assert_called()

    @patch("src.streamwatch.core.stream_checker")
    @patch("src.streamwatch.core.ui")
    def test_refresh_live_streams_general_error(self, mock_ui, mock_stream_checker):
        """Test refresh when general error occurs."""
        mock_stream_manager = Mock()
        mock_stream_manager.load_streams.return_value = [
            {"url": "test_url", "alias": "test_alias"}
        ]
        mock_stream_checker.fetch_live_streams.side_effect = Exception("General error")

        result = _refresh_live_streams(mock_stream_manager)

        assert result == []
        mock_ui.show_message.assert_called()

    @patch("src.streamwatch.core._refresh_live_streams")
    @patch("src.streamwatch.core._show_first_time_welcome")
    @patch("src.streamwatch.core.config")
    @patch("src.streamwatch.core.ui")
    @patch("src.streamwatch.core.MenuHandler")
    @patch("src.streamwatch.core.StreamManager")
    @patch("src.streamwatch.core.PlaybackController")
    def test_run_interactive_loop_first_time(
        self,
        mock_playback_controller_class,
        mock_stream_manager_class,
        mock_menu_handler_class,
        mock_ui,
        mock_config,
        mock_show_welcome,
        mock_refresh,
    ):
        """Test interactive loop for first-time user."""
        # Setup mocks
        mock_config.is_first_run_completed.return_value = False
        mock_config.mark_first_run_completed.return_value = None

        mock_menu_handler = Mock()
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        mock_menu_handler_class.return_value = mock_menu_handler
        mock_stream_manager_class.return_value = mock_stream_manager
        mock_playback_controller_class.return_value = mock_playback_controller

        mock_refresh.return_value = []
        mock_menu_handler.display_main_menu.return_value = None
        mock_menu_handler.handle_user_input.return_value = "q"
        mock_menu_handler.process_menu_choice.return_value = (False, False)  # Exit loop

        run_interactive_loop()

        mock_show_welcome.assert_called_once()
        mock_config.mark_first_run_completed.assert_called_once()
        mock_menu_handler_class.assert_called_once()
        mock_stream_manager_class.assert_called_once()
        mock_playback_controller_class.assert_called_once()

    @patch("src.streamwatch.core._refresh_live_streams")
    @patch("src.streamwatch.core.config")
    @patch("src.streamwatch.core.ui")
    @patch("src.streamwatch.core.MenuHandler")
    @patch("src.streamwatch.core.StreamManager")
    @patch("src.streamwatch.core.PlaybackController")
    def test_run_interactive_loop_normal_user(
        self,
        mock_playback_controller_class,
        mock_stream_manager_class,
        mock_menu_handler_class,
        mock_ui,
        mock_config,
        mock_refresh,
    ):
        """Test interactive loop for normal user."""
        # Setup mocks
        mock_config.is_first_run_completed.return_value = True

        mock_menu_handler = Mock()
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        mock_menu_handler_class.return_value = mock_menu_handler
        mock_stream_manager_class.return_value = mock_stream_manager
        mock_playback_controller_class.return_value = mock_playback_controller

        mock_refresh.return_value = [{"url": "test_url", "username": "test_user"}]
        mock_menu_handler.display_main_menu.return_value = None
        mock_menu_handler.handle_user_input.return_value = "f"
        mock_menu_handler.process_menu_choice.return_value = (False, False)  # Exit loop

        run_interactive_loop()

        mock_refresh.assert_called()
        mock_menu_handler.display_main_menu.assert_called()
        mock_menu_handler.handle_user_input.assert_called()
        mock_menu_handler.process_menu_choice.assert_called()

    @patch("src.streamwatch.core._refresh_live_streams")
    @patch("src.streamwatch.core.config")
    @patch("src.streamwatch.core.ui")
    @patch("src.streamwatch.core.MenuHandler")
    @patch("src.streamwatch.core.StreamManager")
    @patch("src.streamwatch.core.PlaybackController")
    def test_run_interactive_loop_with_refresh(
        self,
        mock_playback_controller_class,
        mock_stream_manager_class,
        mock_menu_handler_class,
        mock_ui,
        mock_config,
        mock_refresh,
    ):
        """Test interactive loop with refresh needed."""
        # Setup mocks
        mock_config.is_first_run_completed.return_value = True

        mock_menu_handler = Mock()
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        mock_menu_handler_class.return_value = mock_menu_handler
        mock_stream_manager_class.return_value = mock_stream_manager
        mock_playback_controller_class.return_value = mock_playback_controller

        mock_refresh.return_value = []
        mock_menu_handler.display_main_menu.return_value = None
        mock_menu_handler.handle_user_input.return_value = "f"

        # First call returns refresh needed, second call exits
        mock_menu_handler.process_menu_choice.side_effect = [
            (True, True),
            (False, False),
        ]

        run_interactive_loop()

        # Should call refresh twice (initial + after refresh request)
        assert mock_refresh.call_count == 2
