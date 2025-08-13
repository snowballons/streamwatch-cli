"""Tests for the MenuHandler class."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch.menu_handler import MenuHandler


class TestMenuHandler:
    """Test MenuHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.menu_handler = MenuHandler()

    def test_init(self):
        """Test MenuHandler initialization."""
        assert self.menu_handler.last_message == ""

    def test_set_message(self):
        """Test setting a message."""
        test_message = "Test message"
        self.menu_handler.set_message(test_message)
        assert self.menu_handler.last_message == test_message

    def test_clear_message(self):
        """Test clearing a message."""
        self.menu_handler.set_message("Test message")
        self.menu_handler.clear_message()
        assert self.menu_handler.last_message == ""

    @patch("src.streamwatch.menu_handler.ui")
    def test_display_main_menu_with_message(self, mock_ui):
        """Test displaying main menu with a message."""
        self.menu_handler.set_message("Success message")
        self.menu_handler.display_main_menu(5)

        # Should print the message with success style
        mock_ui.console.print.assert_called()
        mock_ui.display_main_menu.assert_called_with(5)
        assert self.menu_handler.last_message == ""  # Message should be cleared

    @patch("src.streamwatch.menu_handler.ui")
    def test_display_main_menu_no_streams(self, mock_ui):
        """Test displaying main menu with no live streams."""
        self.menu_handler.display_main_menu(0)

        mock_ui.console.print.assert_called_with(
            "No favorite streams currently live.", style="dimmed"
        )
        mock_ui.display_main_menu.assert_called_with(0)

    @patch("src.streamwatch.menu_handler.ui")
    def test_handle_user_input(self, mock_ui):
        """Test handling user input."""
        mock_ui.prompt_main_menu_action.return_value = "a"

        result = self.menu_handler.handle_user_input()

        assert result == "a"
        mock_ui.prompt_main_menu_action.assert_called_once()

    @patch("src.streamwatch.menu_handler.ui")
    @patch("src.streamwatch.menu_handler.config")
    def test_process_menu_choice_empty_with_streams(self, mock_config, mock_ui):
        """Test processing empty choice with live streams available."""
        mock_ui.select_stream_dialog.return_value = {
            "url": "test_url",
            "username": "test_user",
        }
        mock_config.get_streamlink_quality.return_value = "best"

        mock_stream_manager = Mock()
        mock_playback_controller = Mock()
        mock_playback_controller.start_playback_session.return_value = "stop_playback"

        live_streams = [{"url": "test_url", "username": "test_user"}]

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "", live_streams, mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is False
        assert should_continue is True
        mock_ui.select_stream_dialog.assert_called_once()
        mock_playback_controller.start_playback_session.assert_called_once()

    def test_process_menu_choice_digit_no_streams(self):
        """Test processing digit choice with no live streams."""
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "1", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is False
        assert should_continue is True
        assert "No live streams available" in self.menu_handler.last_message

    def test_process_menu_choice_list_streams(self):
        """Test processing 'l' choice to list streams."""
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "l", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is False
        assert should_continue is True
        mock_stream_manager.list_streams.assert_called_once()

    def test_process_menu_choice_add_streams(self):
        """Test processing 'a' choice to add streams."""
        mock_stream_manager = Mock()
        mock_stream_manager.add_streams.return_value = (True, "Success")
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "a", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is True
        assert should_continue is True
        assert self.menu_handler.last_message == "Success"
        mock_stream_manager.add_streams.assert_called_once()

    def test_process_menu_choice_remove_streams(self):
        """Test processing 'r' choice to remove streams."""
        mock_stream_manager = Mock()
        mock_stream_manager.remove_streams.return_value = (True, "Removed")
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "r", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is True
        assert should_continue is True
        assert self.menu_handler.last_message == "Removed"
        mock_stream_manager.remove_streams.assert_called_once()

    def test_process_menu_choice_import_streams(self):
        """Test processing 'i' choice to import streams."""
        mock_stream_manager = Mock()
        mock_stream_manager.import_streams.return_value = (True, "Imported")
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "i", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is True
        assert should_continue is True
        assert self.menu_handler.last_message == "Imported"
        mock_stream_manager.import_streams.assert_called_once()

    def test_process_menu_choice_export_streams(self):
        """Test processing 'e' choice to export streams."""
        mock_stream_manager = Mock()
        mock_stream_manager.export_streams.return_value = (True, "Exported")
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "e", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is False
        assert should_continue is True
        assert self.menu_handler.last_message == "Exported"
        mock_stream_manager.export_streams.assert_called_once()

    def test_process_menu_choice_refresh(self):
        """Test processing 'f' choice to refresh."""
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "f", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is True
        assert should_continue is True

    @patch("src.streamwatch.menu_handler.ui")
    def test_process_menu_choice_quit(self, mock_ui):
        """Test processing 'q' choice to quit."""
        mock_stream_manager = Mock()
        mock_playback_controller = Mock()

        needs_refresh, should_continue = self.menu_handler.process_menu_choice(
            "q", [], mock_stream_manager, mock_playback_controller
        )

        assert needs_refresh is False
        assert should_continue is False
        mock_ui.clear_screen.assert_called_once()
        mock_ui.console.print.assert_called_with(
            "Exiting StreamWatch. Goodbye!", style="success"
        )

    def test_handle_play_last_stream_in_live_list(self):
        """Test handling play last when stream is in live list."""
        with patch("src.streamwatch.menu_handler.config") as mock_config, patch(
            "src.streamwatch.menu_handler.ui"
        ) as mock_ui:
            mock_config.get_last_played_url.return_value = "test_url"
            mock_config.get_streamlink_quality.return_value = "best"

            live_streams = [{"url": "test_url", "username": "test_user"}]
            mock_playback_controller = Mock()
            mock_playback_controller.start_playback_session.return_value = (
                "stop_playback"
            )

            result, message = self.menu_handler._handle_play_last(
                live_streams, mock_playback_controller
            )

            assert result is None
            assert message == ""
            mock_playback_controller.start_playback_session.assert_called_once()

    def test_handle_play_last_stream_not_live(self):
        """Test handling play last when stream is not live."""
        with patch("src.streamwatch.menu_handler.config") as mock_config, patch(
            "src.streamwatch.menu_handler.ui"
        ) as mock_ui, patch(
            "src.streamwatch.menu_handler.stream_checker"
        ) as mock_stream_checker:
            mock_config.get_last_played_url.return_value = "test_url"
            mock_stream_checker.is_stream_live_for_check.return_value = (False, None)

            live_streams = []
            mock_playback_controller = Mock()

            result, message = self.menu_handler._handle_play_last(
                live_streams, mock_playback_controller
            )

            assert result is None
            assert "currently not live" in message
