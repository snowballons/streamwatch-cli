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
    user_intent_direction = 0  # 0: none, 1: next, -1: previous

    try:
        current_playing_index = [idx for idx, s_info in enumerate(all_live_streams_list) if s_info['url'] == current_stream_info['url']][0]
    except IndexError:
        logger.error("Could not find current stream in live list. Aborting playback session.")
        ui.console.print("[error]Could not find current stream in live list. Aborting playback session.[/error]")
        return "return_to_main"

    while True:
        if not player_process:
            logger.info(f"Attempting to launch stream: {current_stream_info['url']}")

            # --- PRE-PLAYBACK HOOK ---
            player.execute_hook('pre', current_stream_info, current_quality)

            player_process = player.launch_player_process(current_stream_info['url'], current_quality)

            if player_process:
                # --- Successful Launch ---
                user_intent_direction = 0  # Reset intent after a successful launch
                config.set_last_played_url(current_stream_info['url'])
                logger.info(f"Successfully launched. Last played URL set to: {current_stream_info['url']}")
            else:
                # --- POST-PLAYBACK HOOK ON LAUNCH FAILURE ---
                # A launch failure is an "end" to the playback attempt.
                player.execute_hook('post', current_stream_info, current_quality)
                # --- Launch Failed ---
                logger.warning(f"Failed to launch player for {current_stream_info['url']}.")

                # If this was the very first stream the user tried to play, and it failed, then exit.
                if user_intent_direction == 0:
                    ui.show_message("Failed to start player for the selected stream. Returning to main menu.", style="error", duration=2, pause_after=True)
                    return "return_to_main"

                # Otherwise, we were trying to auto-skip, so continue that process.
                ui.console.print(f"Skipping unavailable stream: [info]{current_stream_info['username']}[/info]", style="dimmed")

                # This loop will continue until it finds a playable stream or exhausts the list
                found_playable = False
                for _ in range(len(all_live_streams_list)): # Loop at most the number of streams to prevent infinite loops
                    if user_intent_direction == 1: # Trying to find next
                        current_playing_index = (current_playing_index + 1) % len(all_live_streams_list)
                    elif user_intent_direction == -1: # Trying to find previous
                        current_playing_index = (current_playing_index - 1 + len(all_live_streams_list)) % len(all_live_streams_list)

                    current_stream_info = all_live_streams_list[current_playing_index]
                    ui.console.print(f"Trying next: [info]{current_stream_info['username']}[/info]", style="dimmed")

                    # Attempt to launch the new candidate
                    player_process = player.launch_player_process(current_stream_info['url'], current_quality)
                    if player_process:
                        found_playable = True
                        break # Exit the inner for-loop, continue with the outer while-loop

                if not found_playable:
                    ui.show_message("Could not find any playable streams in the current direction.", style="error", duration=2, pause_after=True)
                    return "return_to_main"

                # If we found a playable stream, the outer while-loop will now continue with a valid player_process
                continue

        # --- Check Player Status (if it's running) ---
        if player_process and player_process.poll() is not None:
            # ... (rest of the function is the same, no changes needed here)
            # ... (code for showing menu and handling actions 's', 'm', 'c', 'd', 'q')
            logger.info("Player process has exited.")
            ui.console.print("\nPlayer has exited.", style="info")
            player.terminate_player_process(player_process) # Ensure it's cleaned up
            player_process = None

            # --- POST-PLAYBACK HOOK ON NORMAL EXIT ---
            player.execute_hook('post', current_stream_info, current_quality)

            return "stop_playback"

        # --- Show Menu and Get User Action ---
        # The logic for has_next_option and has_previous_option is now simplified
        # because the list is circular. There is always a next/previous if list has > 1 item.
        is_navigation_possible = len(all_live_streams_list) > 1
        action = ui.show_playback_menu(current_stream_info['url'], current_quality, is_navigation_possible, is_navigation_possible)

        # --- Handle User Action ---
        if action == "n" or action == "next":
            if is_navigation_possible:
                logger.info("User requested next stream.")
                player.terminate_player_process(player_process)
                player.execute_hook('post', current_stream_info, current_quality) # Hook for the stream that is ending
                player_process = None
                user_intent_direction = 1
                # Use modulo arithmetic for circular list
                current_playing_index = (current_playing_index + 1) % len(all_live_streams_list)
                current_stream_info = all_live_streams_list[current_playing_index]
                current_quality = config.get_streamlink_quality()
            else:
                ui.console.print("No next stream available.", style="warning")
                time.sleep(1)

        elif action == "p" or action == "previous":
            if is_navigation_possible:
                logger.info("User requested previous stream.")
                player.terminate_player_process(player_process)
                player.execute_hook('post', current_stream_info, current_quality) # Hook for the stream that is ending
                player_process = None
                user_intent_direction = -1
                # Modulo arithmetic for circular list (works for negative numbers in Python)
                current_playing_index = (current_playing_index - 1 + len(all_live_streams_list)) % len(all_live_streams_list)
                current_stream_info = all_live_streams_list[current_playing_index]
                current_quality = config.get_streamlink_quality()
            else:
                ui.console.print("No previous stream available.", style="warning")
                time.sleep(1)

        # ... (rest of action handling: s, m, c, d, q) ...
        elif action == "s" or action == "stop":
            logger.info("User stopped playback.")
            player.terminate_player_process(player_process)
            player.execute_hook('post', current_stream_info, current_quality) # Hook
            return "stop_playback"
        elif action == "m" or action == "main_menu":
            logger.info("User returned to main menu from playback.")
            ui.console.print("Stopping stream and returning to main menu...", style="info")
            player.terminate_player_process(player_process)
            player.execute_hook('post', current_stream_info, current_quality) # Hook
            return "return_to_main"
        elif action == "c" or action == "change_quality":
            logger.info("User requested to change stream quality.")
            player.terminate_player_process(player_process)
            player.execute_hook('post', current_stream_info, current_quality) # Hook for the stream that is ending
            player_process = None
            user_intent_direction = 0
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
            player.execute_hook('post', current_stream_info, current_quality) # Hook before quitting
            return "quit_application"
        else:
            time.sleep(0.1)
            continue

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
                elif playback_action == "stop_playback":
                    needs_refresh = False
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
                    elif playback_action == "stop_playback":
                        needs_refresh = False
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

        elif choice == 'i': # IMPORT
            logger.info("User chose to import streams.")
            filepath = ui.prompt_for_filepath("Enter path of .txt file to import from: ")
            if filepath:
                success, message = storage.import_streams_from_txt(filepath)
                last_message = message
                if success:
                    needs_refresh = True # Refresh the list after a successful import
            else:
                last_message = "Import cancelled."

        elif choice == 'e': # EXPORT
            logger.info("User chose to export streams.")
            import time
            default_export_path = f"~/streamwatch_export_{time.strftime('%Y-%m-%d')}.json"
            filepath = ui.prompt_for_filepath("Enter path to save export file: ", default_filename=default_export_path)
            if filepath:
                success, message = storage.export_streams_to_json(filepath)
                last_message = message # Display success or failure message
            else:
                last_message = "Export cancelled."

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
                elif playback_action == "return_to_main":
                    needs_refresh = True
                elif playback_action == "stop_playback":
                    needs_refresh = False
            # If not selected_stream_info_for_last_played, last_message was already set
