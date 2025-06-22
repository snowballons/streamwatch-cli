import subprocess
import sys
from . import config # Assuming ui handles clear_screen now
from . import ui

def play_stream(url_to_play):
    """
    Attempts to play the given stream URL using streamlink and the configured quality.
    """
    ui.clear_screen()
    print(f"Attempting to play: {url_to_play}")
    print(f"Quality: {config.STREAM_QUALITY}")
    print("Press Ctrl+C in the player window (or here if no window opens) to stop.")
    print("--------------------------------------------------------------------")

    command = ["streamlink"]
    if config.TWITCH_DISABLE_ADS:
        command.append("--twitch-disable-ads")
    command.extend([url_to_play, config.STREAM_QUALITY])

    try:
        subprocess.run(command, check=False)
        print("\nPlayer closed or stream ended.")
    except FileNotFoundError:
        # This should ideally be caught by the initial check in main.py
        # but included here as a safeguard during playback attempt.
        print("\nError: streamlink command not found. Cannot play stream.", file=sys.stderr)
        print("Please ensure streamlink is installed and in your system's PATH.", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred while trying to play the stream: {e}", file=sys.stderr)

    input("Press Enter to return to the menu...")