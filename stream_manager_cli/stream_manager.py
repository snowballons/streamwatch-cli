#!/usr/bin/env python3

import subprocess
import re
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
STREAMS_FILE = "streams.txt"  # Path to your stream list file
# CHECK_INTERVAL is no longer used for automatic looping, but kept for potential future use
# CHECK_INTERVAL = 60
STREAMLINK_TIMEOUT = 10       # Seconds to wait for streamlink to respond for liveness check
MAX_WORKERS = 4               # Max concurrent streamlink processes for liveness check
STREAM_QUALITY = "best"       # Quality to pass to streamlink (e.g., "best", "720p", "1080p60")
# --- End Configuration ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def read_streams_from_file(filename):
    """Reads stream URLs from a text file and returns them as a list."""
    try:
        with open(filename, 'r') as file:
            streams = file.readlines()
        return [url.strip() for url in streams if url.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found. Please create it and add stream URLs.")
        # In interactive mode, we might not want to exit immediately,
        # but rather let the user know and retry or quit.
        # For now, returning an empty list allows the main loop to handle it.
        return []
    except Exception as e:
        print(f"Error reading from '{filename}': {e}")
        return []

def is_stream_live_for_check(url):
    """
    Checks if a given stream URL is currently live using streamlink.
    This version is specifically for the liveness check, not for playing.
    Returns a tuple: (bool_is_live, url)
    """
    try:
        process = subprocess.run(
            ["streamlink", "--twitch-disable-ads", url],
            capture_output=True,
            text=True,
            timeout=STREAMLINK_TIMEOUT,
            check=False
        )
        if process.returncode == 0 and "Available streams:" in process.stdout:
            return True, url
        
        stderr_lower = process.stderr.lower()
        stdout_lower = process.stdout.lower()
        if "no playable streams found" in stderr_lower or \
           "error: no streams found on" in stderr_lower or \
           "this stream is offline" in stdout_lower or \
           process.returncode != 0:
            return False, url
        return False, url # Default to not live for ambiguous cases
    except subprocess.TimeoutExpired:
        return False, url
    except FileNotFoundError: # This is a serious issue, should be caught upfront
        raise # Re-raise to be caught by the initial check or fetch_live_streams
    except Exception: # Catch any other exception during the check for a single stream
        return False, url

def fetch_live_streams(all_configured_streams):
    """
    Fetches the list of currently live streams from the configured list.
    Returns a list of live URLs.
    """
    live_streams_found = []
    if not all_configured_streams:
        return []

    print("Checking stream statuses, please wait...")
    # Using ThreadPoolExecutor to check streams concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(is_stream_live_for_check, url): url for url in all_configured_streams}
        
        results_map = {}
        for future in as_completed(future_to_url):
            original_url = future_to_url[future]
            try:
                is_live, _ = future.result()
                results_map[original_url] = is_live
            except FileNotFoundError: # Propagated from is_stream_live_for_check
                print("\nCRITICAL ERROR: streamlink command not found.")
                print("Please ensure streamlink is installed and in your system's PATH.")
                exit(1) # Exit if streamlink isn't found during the check
            except Exception as exc:
                print(f"\nError processing {original_url} during fetch: {exc}")
                results_map[original_url] = False
    
    # Maintain original order from streams.txt for live streams if desired
    for url in all_configured_streams:
        if results_map.get(url, False):
            live_streams_found.append(url)
            
    return live_streams_found

def play_stream(url_to_play):
    """
    Attempts to play the given stream URL using streamlink and the configured quality.
    """
    clear_screen()
    print(f"Attempting to play: {url_to_play}")
    print(f"Quality: {STREAM_QUALITY}")
    print("Press Ctrl+C in the player window (or here if no window opens) to stop.")
    print("--------------------------------------------------------------------")
    try:
        # We let streamlink run in the foreground, so the script waits.
        # MPV (or your default player) should open.
        # check=False because streamlink might exit with non-zero if the stream just died
        # or if the user closes the player early.
        subprocess.run(
            ["streamlink", url_to_play, STREAM_QUALITY],
            check=False
        )
        print("\nPlayer closed or stream ended.")
    except FileNotFoundError:
        print("\nError: streamlink command not found. Cannot play stream.")
        print("Please ensure streamlink is installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn unexpected error occurred while trying to play the stream: {e}")
    
    input("Press Enter to return to the menu...")

def main_interactive_mode():
    """Main interactive loop for the script."""
    current_displayed_live_streams = []
    previously_known_live_set = set()
    needs_refresh = True

    while True:
        if needs_refresh:
            clear_screen()
            print("--- Stream Manager ---")
            all_configured_streams = read_streams_from_file(STREAMS_FILE)
            if not all_configured_streams:
                print(f"\nNo streams configured in '{STREAMS_FILE}' or file not found.")
                print("Please add stream URLs to the file.")
                # Don't set current_displayed_live_streams here yet
            else:
                # fetch_live_streams will print its own "Checking..." message
                newly_fetched_live_list = fetch_live_streams(all_configured_streams)
                newly_fetched_live_set = set(newly_fetched_live_list)

                # --- Identify and print changes ---
                newly_live_now = newly_fetched_live_set - previously_known_live_set
                gone_offline_now = previously_known_live_set - newly_fetched_live_set

                if newly_live_now:
                    print("\n✨ NEWLY LIVE since last refresh:")
                    for url in sorted(list(newly_live_now)): # Sort for consistent display
                        print(f"  [+] {url}")
                
                if gone_offline_now:
                    print("\n👻 GONE OFFLINE since last refresh:")
                    for url in sorted(list(gone_offline_now)): # Sort for consistent display
                        print(f"  [-] {url}")
                
                if not newly_live_now and not gone_offline_now and newly_fetched_live_list:
                    if previously_known_live_set == newly_fetched_live_set : # only print if it's not the first run
                        print("\nNo change in live stream status since last refresh.")


                current_displayed_live_streams = newly_fetched_live_list
                previously_known_live_set = newly_fetched_live_set
            
            needs_refresh = False
            # An empty line for spacing before the stream list or no streams message
            print() 

        # Display streams and menu (even if needs_refresh was false, in case coming back from player)
        if not needs_refresh: # Avoid double clear if refresh just happened
            clear_screen()
            print("--- Stream Manager ---")
            # Re-print change summary if it exists and we are not immediately after a refresh
            # (This part can be tweaked for desired verbosity)


        if not current_displayed_live_streams:
            print("No favorite streams are currently live.")
        else:
            print("--- Available Live Streams ---")
            for i, url in enumerate(current_displayed_live_streams):
                print(f"  [{i+1}] {url}")
        
        print("\n------------------------------------")
        print("Options:")
        if current_displayed_live_streams:
            print("  [number] - Play stream by number")
        print("  [R]      - Refresh live stream list")
        print("  [Q]      - Quit")
        print("------------------------------------")

        choice = input("Enter your choice: ").strip().lower()

        if choice == 'q':
            clear_screen()
            print("Exiting Stream Manager. Goodbye!")
            break
        elif choice == 'r':
            needs_refresh = True
            # Loop will continue and trigger the refresh block
        elif choice.isdigit():
            if not current_displayed_live_streams:
                print("No streams available to play. Try refreshing.")
                time.sleep(2)
                continue

            try:
                stream_idx = int(choice) - 1
                if 0 <= stream_idx < len(current_displayed_live_streams):
                    selected_url = current_displayed_live_streams[stream_idx]
                    play_stream(selected_url)
                    # After playing, the loop will re-render the menu with current streams.
                    # No need to set needs_refresh = True unless user explicitly asks.
                else:
                    print("Invalid stream number. Please try again.")
                    time.sleep(1.5)
            except ValueError: # Should not happen due to isdigit() but good for safety
                print("Invalid input. Please enter a number, 'R', or 'Q'.")
                time.sleep(1.5)
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1.5)

if __name__ == "__main__":
    # Initial check for streamlink
    try:
        subprocess.run(["streamlink", "--version"], capture_output=True, check=True, timeout=5)
    except FileNotFoundError:
        clear_screen()
        print("CRITICAL ERROR: streamlink command not found.")
        print("Please ensure streamlink is installed and in your system's PATH.")
        print("The script cannot continue without it.")
        exit(1)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        clear_screen()
        print(f"CRITICAL ERROR: streamlink found but is not working correctly: {e}")
        print("The script cannot continue.")
        exit(1)
    
    try:
        main_interactive_mode()
    except KeyboardInterrupt:
        clear_screen()
        print("\nScript interrupted by user. Exiting gracefully. Goodbye!")
    except Exception as e:
        clear_screen()
        print(f"\nAn unexpected critical error occurred in the main application: {e}")
        print("If the problem persists, please report it.")