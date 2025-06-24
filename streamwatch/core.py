import time
import sys
import webbrowser
import logging # Import logging
from . import config
from . import storage
from . import stream_checker
from . import player
from . import ui

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".core")

def run_playback_session(initial_stream_info, initial_quality, all_live_streams_list):
    """Manages an active playback session with interactive controls."""
    current_stream_info = initial_stream_info
    current_quality = initial_quality
    player_process = None
    try:
        current_playing_index = [idx for idx, s_info in enumerate(all_live_streams_list) if s_info['url'] == current_stream_info['url']][0]
    except IndexError:
        logger.error("Could not find current stream in live list. Aborting playback session.")
        ui.console.print("[error]Could not find current stream in live list. Aborting playback session.[/error]")
        return "return_to_main"
    while True:
        if player_process and player_process.poll() is not None:
            logger.info("Player has exited.")
            ui.console.print("\nPlayer has exited.", style="info")
            player.terminate_player_process(player_process)
            player_process = None
            return "return_to_main"
        if not player_process:
            player_process = player.launch_player_process(current_stream_info['url'], current_quality)
            if not player_process:
                logger.error("Failed to start player. Returning to main menu.")
                ui.show_message("Failed to start player. Returning to main menu.", style="error", duration=2, pause_after=True)
                return "return_to_main"
            else:
                # Successfully launched, save this as last played
                config.set_last_played_url(current_stream_info['url'])
                logger.info(f"Set last played URL to: {current_stream_info['url']}")
        has_next = (current_playing_index + 1) < len(all_live_streams_list)
        has_previous = current_playing_index > 0
        action = ui.show_playback_menu(current_stream_info['url'], current_quality, has_next, has_previous)
        if action == "s" or action == "stop":
            logger.info("User stopped playback.")
            player.terminate_player_process(player_process)
            return "return_to_main"
        elif action == "m" or action == "main_menu":
            logger.info("User returned to main menu from playback.")
            ui.console.print("Stopping stream and returning to main menu...", style="info")
            player.terminate_player_process(player_process)
            return "return_to_main"
        elif action == "n" or action == "next":
            if has_next:
                logger.info("User switched to next stream.")
                player.terminate_player_process(player_process)
                player_process = None
                current_playing_index += 1
                current_stream_info = all_live_streams_list[current_playing_index]
                current_quality = config.get_streamlink_quality()
            else:
                logger.warning("No next stream available.")
                ui.console.print("No next stream available.", style="warning")
                time.sleep(1)
        elif action == "p" or action == "previous":
            if has_previous:
                logger.info("User switched to previous stream.")
                player.terminate_player_process(player_process)
                player_process = None
                current_playing_index -= 1
                current_stream_info = all_live_streams_list[current_playing_index]
                current_quality = config.get_streamlink_quality()
            else:
                logger.warning("No previous stream available.")
                ui.console.print("No previous stream available.", style="warning")
                time.sleep(1)
        elif action == "c" or action == "change_quality":
            logger.info("User requested to change stream quality.")
            player.terminate_player_process(player_process)
            player_process = None
            available_qualities = player.fetch_available_qualities(current_stream_info['url'])
            if available_qualities:
                new_quality = ui.select_quality_dialog(available_qualities, current_quality)
                if new_quality:
                    logger.info(f"User changed quality to {new_quality}.")
                    current_quality = new_quality
            else:
                logger.warning(f"Could not fetch qualities for {current_stream_info['url']}")
                ui.console.print(f"Could not fetch qualities for {current_stream_info['url']}", style="warning")
                time.sleep(1.5)
        elif action == "d" or action == "donate":
            try:
                donation_url = config.get_donation_link()
                logger.info(f"User opened donation link: {donation_url}")
                ui.console.print(f"Opening donation link: [link={donation_url}]{donation_url}[/link]", style="info")
                webbrowser.open(donation_url)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Could not open donation link: {e}", exc_info=True)
                ui.console.print(f"[error]Could not open donation link: {e}[/error]")
                time.sleep(1.5)
        elif action == "q" or action == "quit":
            logger.info("User quit application from playback session.")
            player.terminate_player_process(player_process)
            return "quit_application"
        else:
            if player_process and player_process.poll() is None:
                time.sleep(0.1)
                continue
            else:
                logger.info("Player seems to have exited unexpectedly.")
                ui.console.print("\nPlayer seems to have exited.", style="info")
                return "return_to_main"

def run_interactive_loop():
    logger.info("Starting interactive loop.")
    # --- First-Time User Experience Check ---
    if not config.is_first_run_completed():
        ui.clear_screen()
        ui.console.print("--- Welcome to StreamWatch! ---", style="bold white on blue")
        ui.console.print("\nIt looks like this is your first time, or your stream list is empty.")
        ui.console.print("To get started, manage your favorite stream URLs using the menu options:")
        ui.console.print("  - Press [bold yellow]A[/bold yellow] to Add new streams.")
        ui.console.print("  - Once added, press [bold yellow]F[/bold yellow] to Refresh and see who's live.")
        ui.console.print("\nEnjoy watching!")
        ui.show_message("", duration=0, pause_after=True) # Pause for user to read
        config.mark_first_run_completed()
        logger.info("First run experience completed and marked.")
        needs_refresh = True 
    else:
        needs_refresh = True # Default to refresh on normal startup

    live_streams = []
    previously_live_set = set()
    last_message = ""

    while True:
        if needs_refresh:
            ui.clear_screen()
            ui.console.print(f"--- {config.APP_NAME} ---", style="title") # Use APP_NAME
            all_streams = storage.load_streams() # Load/Re-load streams
            logger.debug(f"Loaded {len(all_streams)} streams from storage.")
            if not all_streams:
                logger.info("No streams configured yet.")
                ui.console.print("\nNo streams configured yet.", style="warning")
                ui.console.print("Use the 'Add' option [A] to add your favorite stream URLs.", style="info")
                live_streams = [] # Ensure live list is empty if no streams configured
                previously_live_set = set()
            else:
                try:
                    live_streams = stream_checker.fetch_live_streams(all_streams)
                    newly_fetched_live_urls_set = set([s['url'] for s in live_streams])
                    previously_live_set = newly_fetched_live_urls_set
                except FileNotFoundError as e:
                    logger.critical(f"ERROR: {e}. Please ensure streamlink is installed.", exc_info=True)
                    ui.show_message(f"ERROR: {e}. Please ensure streamlink is installed.", duration=0, pause_after=True)
                    sys.exit(1) # Cannot continue without streamlink
                except Exception as e:
                    logger.exception(f"An error occurred during stream check: {e}")
                    ui.show_message(f"An error occurred during stream check: {e}", duration=0, pause_after=True)
                    # Decide whether to proceed with potentially stale data or halt
                    live_streams = [] # Clear live streams on error
                    previously_live_set = set()

            needs_refresh = False
            last_message = "" # Clear previous message on refresh
            ui.console.print()

        # Display current status and menu
        if not needs_refresh: # Avoid double clear if refresh just happened
            ui.clear_screen()
            ui.console.print("--- StreamWatch ---", style="title")

        if last_message:
            # Style based on message content
            msg_style = "info"
            if "error" in last_message.lower() or "fail" in last_message.lower():
                msg_style = "error"
            elif "success" in last_message.lower():
                msg_style = "success"
            elif "warn" in last_message.lower():
                msg_style = "warning"
            ui.console.print(f"\n{last_message}\n", style=msg_style)
            last_message = ""

        if not live_streams:
            ui.console.print("No favorite streams currently live.", style="dimmed")
        else:
            # Display_stream_list is now more of a static display before the menu prompt
            ui.display_stream_list(live_streams, title="--- Live Streams ---")

        ui.display_main_menu(len(live_streams))
        choice = ui.prompt_main_menu_action()

        # Process choice
        # If user just presses Enter and live streams exist, trigger selection
        if not choice and live_streams: # Empty input and streams are available
            selected_stream_info = ui.select_stream_dialog(live_streams, title="Select Live Stream")
            if selected_stream_info:
                logger.info(f"User selected stream: {selected_stream_info['url']}")
                playback_action = run_playback_session(selected_stream_info, config.get_streamlink_quality(), live_streams)
                if playback_action == "quit_application":
                    logger.info("User quit application from main menu.")
                    ui.clear_screen()
                    ui.console.print("Exiting StreamWatch. Goodbye!", style="success")
                    sys.exit(0)
                elif playback_action == "return_to_main":
                    needs_refresh = True
                last_message = ""
            else:
                logger.info("Play operation cancelled or no stream selected.")
                last_message = "Play operation cancelled or no stream selected."
        
        elif choice.isdigit(): # If they still type a number at main menu
            if not live_streams:
                logger.warning("No live streams available to play.")
                last_message = "No live streams available to play."
                continue
            try:
                stream_idx = int(choice) - 1
                if 0 <= stream_idx < len(live_streams):
                    selected_stream_info = live_streams[stream_idx]
                    logger.info(f"User selected stream by number: {selected_stream_info['url']}")
                    playback_action = run_playback_session(selected_stream_info, config.get_streamlink_quality(), live_streams)
                    if playback_action == "quit_application":
                        logger.info("User quit application from main menu.")
                        ui.clear_screen()
                        ui.console.print("Exiting StreamWatch. Goodbye!", style="success")
                        sys.exit(0)
                    elif playback_action == "return_to_main":
                        needs_refresh = True
                    last_message = ""
                else:
                    logger.warning("Invalid live stream number selected.")
                    last_message = "Invalid live stream number."
            except ValueError:
                logger.warning("Invalid input for stream selection.")
                last_message = "Invalid input."

        elif choice == 'l':
             logger.info("User listed all configured streams.")
             ui.clear_screen()
             current_all_stream_urls = storage.load_streams() # This returns a list of URL strings
             ui.display_stream_list(current_all_stream_urls, title="--- All Configured Streams ---")
             ui.show_message("", duration=0, pause_after=True)

        elif choice == 'a':
            logger.info("User chose to add new streams.")
            new_urls_to_add = ui.prompt_add_streams() # Uses new prompt
            if new_urls_to_add:
                success, message = storage.add_streams(new_urls_to_add)
                last_message = message
                if success:
                    logger.info("Streams added successfully.")
                    needs_refresh = True
            else:
                logger.info("Add operation cancelled or no URLs entered.")
                last_message = "Add operation cancelled or no URLs entered."

        elif choice == 'r':
             logger.info("User chose to remove streams.")
             current_all_streams = storage.load_streams()
             # Use the new dialog/prompt for removal
             indices_to_remove = ui.prompt_remove_streams_dialog(current_all_streams) # Updated call
             if indices_to_remove is not None and indices_to_remove: # Check for None (cancel) and empty list
                 success, message = storage.remove_streams_by_indices(indices_to_remove)
                 last_message = message
                 if success:
                     logger.info("Streams removed successfully.")
                     needs_refresh = True
             elif indices_to_remove is None: # Explicit cancel from dialog
                 logger.info("Remove operation cancelled.")
                 last_message = "Remove operation cancelled."
             else: # Empty list returned (no valid indices entered or no streams to remove)
                 if current_all_streams: # Only say "no valid indices" if there were streams to pick from
                    logger.info("No valid streams selected for removal.")
                    last_message = "No valid streams selected for removal."

        elif choice == 'f':
            logger.info("User refreshed live stream list.")
            needs_refresh = True

        elif choice == 'q':
            logger.info("User quit application from main menu.")
            ui.clear_screen()
            ui.console.print("Exiting StreamWatch. Goodbye!", style="success")
            break

        elif choice == 'p' and config.get_last_played_url(): # Play Last
            last_played_url = config.get_last_played_url()
            logger.info(f"Attempting to play last played stream: {last_played_url}")
            ui.console.print(f"Checking status for last played: [info]{last_played_url}[/info]")
            found_in_live = next((s_info for s_info in live_streams if s_info['url'] == last_played_url), None)
            selected_stream_info_for_last_played = None
            if found_in_live:
                logger.debug("Last played stream is in current live list.")
                selected_stream_info_for_last_played = found_in_live
            else:
                ui.console.print(f"Last played stream not in current live list. Checking '{last_played_url}' specifically...", style="dimmed")
                is_live_now, _ = stream_checker.is_stream_live_for_check(last_played_url)
                if is_live_now:
                    logger.info(f"Last played stream '{last_played_url}' is live. Fetching details...")
                    temp_list_for_details = [last_played_url]
                    detailed_info_list = stream_checker.fetch_live_streams(temp_list_for_details)
                    if detailed_info_list:
                        selected_stream_info_for_last_played = detailed_info_list[0]
                    else:
                        last_message = f"Could not fetch details for live stream: {last_played_url}"
                        logger.warning(last_message)
                else:
                    last_message = f"Last played stream '{last_played_url}' is currently not live."
                    logger.info(last_message)
            if selected_stream_info_for_last_played:
                playback_action = run_playback_session(
                    selected_stream_info_for_last_played, 
                    config.get_streamlink_quality(), # Use configured quality
                    live_streams # Pass current full live list for next/prev context
                )
                if playback_action == "quit_application":
                    ui.clear_screen()
                    ui.console.print("Exiting StreamWatch. Goodbye!", style="success")
                    sys.exit(0)
                needs_refresh = True # Refresh after playback
            # If not selected_stream_info_for_last_played, last_message was already set