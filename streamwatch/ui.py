import os
import time

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_main_menu(live_streams_count):
    """Displays the main menu options."""
    print("\n------------------------------------")
    print("Options:")
    if live_streams_count > 0:
        print("  [number] - Play live stream by number")
    print("  [L]      - List all configured streams")
    print("  [A]      - Add new stream URL(s)")
    if live_streams_count > 0: # Only show remove if there's something to remove from the *displayed* list
       pass # Decide if Remove should operate on live list or all configured list
    print("  [R]      - Remove configured stream(s)") # Changed to operate on all configured streams
    print("  [F]      - Refresh live stream list")
    print("  [Q]      - Quit")
    print("------------------------------------")

def display_stream_list(stream_list, title="--- Available Streams ---", show_numbers=True):
    """Displays a list of streams, optionally numbered."""
    print(title)
    if not stream_list:
        print("  (No streams to display)")
        return

    for i, url in enumerate(stream_list):
        if show_numbers:
            print(f"  [{i+1}] {url}")
        else:
             print(f"  - {url}")

def prompt_for_action(prompt_text="Enter your choice: "):
    """Gets user input for menu actions."""
    return input(prompt_text).strip().lower()

def prompt_add_streams():
    """Prompts the user to enter stream URLs to add."""
    print("\nEnter stream URL(s) to add.")
    print("You can add multiple URLs separated by commas (,).")
    urls_input = input("URL(s): ").strip()
    if not urls_input:
        return []
    # Split by comma and strip whitespace from each potential URL
    return [url.strip() for url in urls_input.split(',') if url.strip()]

def prompt_remove_streams(all_streams):
    """Displays all streams and prompts the user to select which to remove."""
    if not all_streams:
        print("\nNo streams configured to remove.")
        time.sleep(1.5)
        return []

    clear_screen()
    display_stream_list(all_streams, title="--- Configured Streams ---", show_numbers=True)
    print("\nEnter the number(s) of the stream(s) you want to remove.")
    print("You can enter multiple numbers separated by spaces or commas (e.g., 1 3 4 or 1,3,4).")
    print("Enter 'C' to cancel.")

    while True:
        choice = input("Remove number(s): ").strip().lower()
        if choice == 'c':
            return [] # User cancelled

        # Process input: replace commas with spaces, split by space
        try:
            raw_indices = choice.replace(',', ' ').split()
            # Convert to integers (adjusting for 1-based display)
            indices_to_remove = [int(idx) - 1 for idx in raw_indices if idx.isdigit()]

            # Validate indices
            valid_indices = []
            invalid_inputs = []
            for i, original_input in enumerate(raw_indices):
                 if original_input.isdigit():
                     idx_val = int(original_input) - 1
                     if 0 <= idx_val < len(all_streams):
                         valid_indices.append(idx_val)
                     else:
                         invalid_inputs.append(original_input)
                 elif original_input: # Non-digit, non-empty input
                    invalid_inputs.append(original_input)

            if not valid_indices and invalid_inputs:
                 print(f"Invalid input: {', '.join(invalid_inputs)}. Please enter valid numbers or 'C'.")
                 continue # Ask again
            elif invalid_inputs:
                 print(f"Warning: Ignored invalid input(s): {', '.join(invalid_inputs)}")
                 # Proceed with valid indices if any

            if not valid_indices and not invalid_inputs: # User entered nothing or just spaces
                 print("No valid numbers entered. Please try again or enter 'C' to cancel.")
                 continue

            return list(set(valid_indices)) # Return unique valid 0-based indices

        except ValueError:
            print("Invalid input format. Please enter numbers separated by spaces/commas, or 'C'.")
            # Loop continues

def show_message(message, duration=1.5, pause_after=False):
    """Displays a message for a short duration."""
    print(f"\n{message}")
    if duration > 0:
        time.sleep(duration)
    if pause_after:
        input("\nPress Enter to continue...")