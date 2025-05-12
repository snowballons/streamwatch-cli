import time
import sys
from . import config
from . import storage
from . import stream_checker
from . import player
from . import ui

def run_interactive_loop():
    """Main interactive loop for the stream manager."""
    live_streams = []
    all_streams = storage.load_streams() # Load initially
    previously_live_set = set()
    needs_refresh = True
    last_message = ""

    while True:
        if needs_refresh:
            ui.clear_screen()
            print("--- Stream Manager ---")
            all_streams = storage.load_streams() # Re-load in case file changed externally or after add/remove
            if not all_streams:
                print("\nNo streams configured yet.")
                print("Use the 'Add' option [A] to add your favorite stream URLs.")
                live_streams = [] # Ensure live list is empty if no streams configured
                previously_live_set = set()
            else:
                try:
                    newly_fetched_live_list = stream_checker.fetch_live_streams(all_streams)
                    newly_fetched_live_set = set(newly_fetched_live_list)

                    # --- Identify and print changes ---
                    newly_live_now = newly_fetched_live_set - previously_live_set
                    gone_offline_now = previously_live_set - newly_fetched_live_set

                    if newly_live_now:
                        print("\n✨ NEWLY LIVE since last refresh:")
                        for url in sorted(list(newly_live_now)):
                            print(f"  [+] {url}")
                    if gone_offline_now:
                        print("\n👻 GONE OFFLINE since last refresh:")
                        for url in sorted(list(gone_offline_now)):
                            print(f"  [-] {url}")
                    # Avoid "no change" message on first load or if lists changed
                    if not newly_live_now and not gone_offline_now and previously_live_set and previously_live_set == newly_fetched_live_set:
                         print("\nNo change in live stream status since last refresh.")

                    live_streams = newly_fetched_live_list
                    previously_live_set = newly_fetched_live_set
                except FileNotFoundError as e:
                    ui.show_message(f"ERROR: {e}. Please ensure streamlink is installed.", duration=0, pause_after=True)
                    sys.exit(1) # Cannot continue without streamlink
                except Exception as e:
                    ui.show_message(f"An error occurred during stream check: {e}", duration=0, pause_after=True)
                    # Decide whether to proceed with potentially stale data or halt
                    live_streams = [] # Clear live streams on error
                    previously_live_set = set()


            needs_refresh = False
            last_message = "" # Clear previous message on refresh
            print()

        # Display current status and menu
        if not needs_refresh: # Avoid double clear if refresh just happened
            ui.clear_screen()
            print("--- Stream Manager ---")

        if last_message:
            print(f"\n{last_message}\n")
            last_message = "" # Show message only once

        if not live_streams:
            print("No favorite streams currently live.")
        else:
            ui.display_stream_list(live_streams, title="--- Live Streams ---", show_numbers=True)

        ui.display_main_menu(len(live_streams))
        choice = ui.prompt_for_action()

        # Process choice
        if choice.isdigit():
            if not live_streams:
                last_message = "No live streams available to play."
                continue
            try:
                stream_idx = int(choice) - 1
                if 0 <= stream_idx < len(live_streams):
                    selected_url = live_streams[stream_idx]
                    player.play_stream(selected_url)
                    # Loop continues, re-displaying the menu
                else:
                    last_message = "Invalid live stream number."
            except ValueError:
                last_message = "Invalid input."

        elif choice == 'l':
             ui.clear_screen()
             current_all_streams = storage.load_streams() # Get latest list
             ui.display_stream_list(current_all_streams, title="--- All Configured Streams ---", show_numbers=False)
             ui.show_message("", duration=0, pause_after=True) # Pause to view list


        elif choice == 'a':
            new_urls_to_add = ui.prompt_add_streams()
            if new_urls_to_add:
                success, message = storage.add_streams(new_urls_to_add)
                last_message = message
                if success:
                    needs_refresh = True # Refresh list after successful add
            else:
                last_message = "Add operation cancelled or no URLs entered."

        elif choice == 'r':
             current_all_streams = storage.load_streams() # Get latest list for removal prompt
             indices_to_remove = ui.prompt_remove_streams(current_all_streams)
             if indices_to_remove:
                 success, message = storage.remove_streams_by_indices(indices_to_remove)
                 last_message = message
                 if success:
                     needs_refresh = True # Refresh list after successful removal
             else:
                 last_message = "Remove operation cancelled or no valid indices entered."


        elif choice == 'f':
            needs_refresh = True

        elif choice == 'q':
            ui.clear_screen()
            print("Exiting Stream Manager. Goodbye!")
            break

        else:
            last_message = "Invalid choice. Please try again."