import logging  # Import logging
import sys
from typing import Any, Dict, List

from . import config, stream_checker, ui
from .menu_handler import MenuHandler
from .playback_controller import PlaybackController
from .stream_manager import StreamManager

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".core")


# This function is now handled by PlaybackController.start_playback_session()
# Keeping a wrapper for backward compatibility during transition
def run_playback_session(
    initial_stream_info: Dict[str, Any],
    initial_quality: str,
    all_live_streams_list: List[Dict[str, Any]],
) -> str:
    """Wrapper for PlaybackController.start_playback_session() - deprecated."""
    playback_controller = PlaybackController()
    return playback_controller.start_playback_session(
        initial_stream_info, initial_quality, all_live_streams_list
    )


def run_interactive_loop() -> None:
    """Main interactive loop for the StreamWatch application."""
    logger.info("Starting interactive loop.")

    # Initialize the new modules
    menu_handler = MenuHandler()
    stream_manager = StreamManager()
    playback_controller = PlaybackController()

    # --- First-Time User Experience Check ---
    if not config.is_first_run_completed():
        _show_first_time_welcome()
        config.mark_first_run_completed()
        logger.info("First run experience completed and marked.")
        needs_refresh = True
    else:
        needs_refresh = True  # Default to refresh on normal startup

    live_streams: List[Dict[str, Any]] = []

    while True:
        if needs_refresh:
            live_streams = _refresh_live_streams(stream_manager)
            needs_refresh = False
            menu_handler.clear_message()

        # Display current status and menu
        if not needs_refresh:  # Avoid double clear if refresh just happened
            ui.clear_screen()
            ui.console.print("--- StreamWatch ---", style="title")

        if not live_streams:
            ui.console.print("No favorite streams currently live.", style="dimmed")
        else:
            # Use pagination-aware display method
            menu_handler.display_streams_with_pagination(live_streams, title="--- Live Streams ---")

        menu_handler.display_main_menu(len(live_streams))
        choice = menu_handler.handle_user_input()

        # Process choice using MenuHandler
        needs_refresh, should_continue = menu_handler.process_menu_choice(
            choice, live_streams, stream_manager, playback_controller
        )

        if not should_continue:
            break


def _show_first_time_welcome() -> None:
    """Display the first-time user welcome message."""
    ui.clear_screen()
    ui.console.print("--- Welcome to StreamWatch! ---", style="bold white on blue")
    ui.console.print(
        "\nIt looks like this is your first time, or your stream list is empty."
    )
    ui.console.print(
        "To get started, manage your favorite stream URLs using the menu options:"
    )
    ui.console.print("  - Press [bold yellow]A[/bold yellow] to Add new streams.")
    ui.console.print(
        "  - Once added, press [bold yellow]F[/bold yellow] to Refresh and see who's live."
    )
    ui.console.print("\nEnjoy watching!")
    ui.show_message("", duration=0, pause_after=True)  # Pause for user to read


def _refresh_live_streams(stream_manager: StreamManager) -> List[Dict[str, Any]]:
    """Refresh the list of live streams."""
    ui.clear_screen()
    ui.console.print(f"--- {config.APP_NAME} ---", style="title")

    all_streams = stream_manager.load_streams()
    logger.debug(f"Loaded {len(all_streams)} streams from storage.")

    if not all_streams:
        logger.info("No streams configured yet.")
        ui.console.print("\nNo streams configured yet.", style="warning")
        ui.console.print(
            "Use the 'Add' option [A] to add your favorite stream URLs.",
            style="info",
        )
        return []

    try:
        live_streams = stream_checker.fetch_live_streams(all_streams)
        ui.console.print()
        return live_streams
    except FileNotFoundError as e:
        logger.critical(
            f"ERROR: {e}. Please ensure streamlink is installed.",
            exc_info=True,
        )
        ui.show_message(
            f"ERROR: {e}. Please ensure streamlink is installed.",
            duration=0,
            pause_after=True,
        )
        sys.exit(1)  # Cannot continue without streamlink
    except Exception as e:
        logger.exception(f"An error occurred during stream check: {e}")
        ui.show_message(
            f"An error occurred during stream check: {e}",
            duration=0,
            pause_after=True,
        )
        return []  # Clear live streams on error
