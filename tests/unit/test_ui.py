"""
Unit tests for UI components module.
"""
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.streamwatch import ui


class TestScreenManagement:
    """Test screen management functionality."""

    def test_clear_screen_windows(self, mock_subprocess_run):
        """Test screen clearing on Windows."""
        with patch("os.name", "nt"):
            ui.clear_screen()
            mock_subprocess_run.assert_called_once()
            call_args = mock_subprocess_run.call_args[0][0]
            assert "cls" in call_args

    def test_clear_screen_unix(self, mock_subprocess_run):
        """Test screen clearing on Unix systems."""
        with patch("os.name", "posix"):
            ui.clear_screen()
            mock_subprocess_run.assert_called_once()
            call_args = mock_subprocess_run.call_args[0][0]
            assert "clear" in call_args

    def test_clear_screen_error_handling(self, mock_subprocess_run):
        """Test screen clearing error handling."""
        mock_subprocess_run.side_effect = Exception("Command failed")

        # Should not raise exception
        ui.clear_screen()


class TestFilePathPrompting:
    """Test file path prompting functionality."""

    @patch("src.streamwatch.ui.prompt")
    def test_prompt_for_filepath_success(self, mock_prompt):
        """Test successful file path prompting."""
        mock_prompt.return_value = "/path/to/file.txt"

        result = ui.prompt_for_filepath("Enter file path: ")
        assert result == "/path/to/file.txt"

    @patch("src.streamwatch.ui.prompt")
    def test_prompt_for_filepath_empty(self, mock_prompt):
        """Test file path prompting with empty input."""
        mock_prompt.return_value = ""

        result = ui.prompt_for_filepath("Enter file path: ")
        assert result is None

    @patch("src.streamwatch.ui.prompt")
    def test_prompt_for_filepath_cancelled(self, mock_prompt):
        """Test file path prompting when cancelled."""
        mock_prompt.side_effect = KeyboardInterrupt()

        result = ui.prompt_for_filepath("Enter file path: ")
        assert result is None

    @patch("src.streamwatch.ui.prompt")
    def test_prompt_for_filepath_eof(self, mock_prompt):
        """Test file path prompting with EOF."""
        mock_prompt.side_effect = EOFError()

        result = ui.prompt_for_filepath("Enter file path: ")
        assert result is None


class TestMainMenuDisplay:
    """Test main menu display functionality."""

    def test_display_main_menu_no_streams(self):
        """Test main menu display with no live streams."""
        # Should not raise exception
        ui.display_main_menu(0)

    def test_display_main_menu_with_streams(self):
        """Test main menu display with live streams."""
        # Should not raise exception
        ui.display_main_menu(5)


class TestViewerCountFormatting:
    """Test viewer count formatting functionality."""

    def test_format_viewer_count_none(self):
        """Test formatting None viewer count."""
        result = ui.format_viewer_count(None)
        assert result == ""

    def test_format_viewer_count_small(self):
        """Test formatting small viewer count."""
        result = ui.format_viewer_count(123)
        assert result == "123"

    def test_format_viewer_count_thousands(self):
        """Test formatting thousands viewer count."""
        result = ui.format_viewer_count(1234)
        assert result == "1.2K"

    def test_format_viewer_count_millions(self):
        """Test formatting millions viewer count."""
        result = ui.format_viewer_count(1234567)
        assert result == "1.2M"

    def test_format_viewer_count_invalid_type(self):
        """Test formatting invalid viewer count type."""
        result = ui.format_viewer_count("invalid")
        assert result == ""


class TestStreamFormatting:
    """Test stream formatting functionality."""

    def test_format_stream_for_display_basic(self, mock_live_stream_info):
        """Test basic stream formatting."""
        stream = mock_live_stream_info[0]
        result = ui.format_stream_for_display(stream, index=0)

        # Should return Text object
        assert result is not None

    def test_format_stream_for_display_prompt_toolkit(self, mock_live_stream_info):
        """Test stream formatting for prompt toolkit."""
        stream = mock_live_stream_info[0]
        result = ui.format_stream_for_display(stream, index=0, for_prompt_toolkit=True)

        # Should return string when for_prompt_toolkit=True
        assert isinstance(result, str)

    def test_format_stream_for_display_no_index(self, mock_live_stream_info):
        """Test stream formatting without index."""
        stream = mock_live_stream_info[0]
        result = ui.format_stream_for_display(stream)

        assert result is not None

    def test_format_stream_for_display_invalid_data(self):
        """Test stream formatting with invalid data."""
        invalid_stream = {"invalid": "data"}
        result = ui.format_stream_for_display(invalid_stream)

        # Should handle gracefully
        assert result is not None


class TestStreamListDisplay:
    """Test stream list display functionality."""

    def test_display_stream_list_empty(self):
        """Test displaying empty stream list."""
        # Should not raise exception
        ui.display_stream_list([])

    def test_display_stream_list_with_streams(self, mock_live_stream_info):
        """Test displaying stream list with streams."""
        # Should not raise exception
        ui.display_stream_list(mock_live_stream_info)

    def test_display_stream_list_custom_title(self, mock_live_stream_info):
        """Test displaying stream list with custom title."""
        # Should not raise exception
        ui.display_stream_list(mock_live_stream_info, title="Custom Title")


class TestStreamSelection:
    """Test stream selection functionality."""

    @patch("src.streamwatch.ui.radiolist_dialog")
    def test_select_stream_dialog_success(self, mock_dialog, mock_live_stream_info):
        """Test successful stream selection."""
        mock_dialog_instance = Mock()
        mock_dialog_instance.run.return_value = mock_live_stream_info[0]
        mock_dialog.return_value = mock_dialog_instance

        result = ui.select_stream_dialog(mock_live_stream_info)
        assert result == mock_live_stream_info[0]

    @patch("src.streamwatch.ui.radiolist_dialog")
    def test_select_stream_dialog_cancelled(self, mock_dialog, mock_live_stream_info):
        """Test cancelled stream selection."""
        mock_dialog_instance = Mock()
        mock_dialog_instance.run.return_value = None
        mock_dialog.return_value = mock_dialog_instance

        result = ui.select_stream_dialog(mock_live_stream_info)
        assert result is None

    @patch("src.streamwatch.ui.message_dialog")
    def test_select_stream_dialog_empty_list(self, mock_message_dialog):
        """Test stream selection with empty list."""
        result = ui.select_stream_dialog([])
        assert result is None
        mock_message_dialog.assert_called_once()


class TestStreamAddition:
    """Test stream addition functionality."""

    @patch("builtins.input")
    def test_prompt_add_streams_success(self, mock_input):
        """Test successful stream addition prompting."""
        mock_input.side_effect = [
            "https://www.twitch.tv/testuser Test User",
            "https://www.youtube.com/@testchannel",
            "",  # Empty line to finish
        ]

        result = ui.prompt_add_streams()
        assert len(result) == 2
        assert result[0]["url"] == "https://www.twitch.tv/testuser"
        assert result[0]["alias"] == "Test User"

    @patch("builtins.input")
    def test_prompt_add_streams_cancelled(self, mock_input):
        """Test cancelled stream addition."""
        mock_input.side_effect = KeyboardInterrupt()

        result = ui.prompt_add_streams()
        assert result == []

    @patch("builtins.input")
    def test_prompt_add_streams_eof(self, mock_input):
        """Test stream addition with EOF."""
        mock_input.side_effect = EOFError()

        result = ui.prompt_add_streams()
        assert result == []


class TestMenuActions:
    """Test menu action functionality."""

    @patch("builtins.input")
    def test_prompt_main_menu_action_success(self, mock_input):
        """Test successful main menu action prompting."""
        mock_input.return_value = "1"

        result = ui.prompt_main_menu_action()
        assert result == "1"

    @patch("builtins.input")
    def test_prompt_main_menu_action_cancelled(self, mock_input):
        """Test cancelled main menu action."""
        mock_input.side_effect = KeyboardInterrupt()

        result = ui.prompt_main_menu_action()
        assert result == "q"

    @patch("builtins.input")
    def test_prompt_main_menu_action_empty(self, mock_input):
        """Test empty main menu action input."""
        mock_input.return_value = ""

        result = ui.prompt_main_menu_action()
        assert result == ""


class TestMessageDisplay:
    """Test message display functionality."""

    def test_show_message_basic(self):
        """Test basic message display."""
        # Should not raise exception
        ui.show_message("Test message")

    def test_show_message_with_style(self):
        """Test message display with custom style."""
        # Should not raise exception
        ui.show_message("Test message", style="error")

    def test_show_message_no_duration(self):
        """Test message display with no duration."""
        # Should not raise exception
        ui.show_message("Test message", duration=0)

    def test_show_message_with_pause(self):
        """Test message display with pause after."""
        with patch("src.streamwatch.ui.prompt") as mock_prompt:
            mock_prompt.return_value = ""
            ui.show_message("Test message", pause_after=True)
            mock_prompt.assert_called_once()
