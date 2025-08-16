"""Tests for the main application entry point and orchestration."""

from unittest.mock import Mock, patch

import pytest

from src.streamwatch.app import StreamWatchApp


@patch("src.streamwatch.app.StreamWatchApp._run_interactive_loop")
def test_app_run_handles_keyboard_interrupt(mock_loop):
    """Verify the app's main run method can be started and handles KeyboardInterrupt."""
    # Simulate the user pressing Ctrl+C during the loop
    mock_loop.side_effect = KeyboardInterrupt()

    app = StreamWatchApp()

    # The run method should catch the interrupt and not raise an exception
    try:
        app.run()
    except KeyboardInterrupt:
        pytest.fail("The app.run() method did not catch the KeyboardInterrupt.")


@patch("src.streamwatch.app.DIContainer")
def test_app_initialization(mock_container):
    """Verify that the StreamWatchApp initializes its components correctly."""
    app = StreamWatchApp()

    # Verify that the container was instructed to get the core components
    container_instance = app.get_container()
    container_instance.get.assert_any_call("menu_handler")
    container_instance.get.assert_any_call("stream_manager")
    container_instance.get.assert_any_call("playback_controller")
