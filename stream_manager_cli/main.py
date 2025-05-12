import subprocess
import sys
from . import core
from . import ui # For clear_screen

def initial_streamlink_check():
    """Checks if streamlink command is available and executable."""
    try:
        # Use --version as a lightweight check
        subprocess.run(["streamlink", "--version"], capture_output=True, check=True, timeout=5)
        return True
    except FileNotFoundError:
        print("CRITICAL ERROR: streamlink command not found.", file=sys.stderr)
        print("Please ensure streamlink is installed and in your system's PATH.", file=sys.stderr)
        return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"CRITICAL ERROR: streamlink found but is not working correctly: {e}", file=sys.stderr)
        return False
    except Exception as e: # Catch any other unexpected errors
        print(f"CRITICAL ERROR: An unexpected issue occurred while checking for streamlink: {e}", file=sys.stderr)
        return False

def main():
    """Entry point for the Stream Manager CLI application."""
    if not initial_streamlink_check():
        print("\nThe script cannot continue without a working streamlink installation.", file=sys.stderr)
        sys.exit(1)

    try:
        core.run_interactive_loop()
    except KeyboardInterrupt:
        ui.clear_screen()
        print("\nScript interrupted by user. Exiting gracefully. Goodbye!")
    except Exception as e:
        ui.clear_screen()
        # Try to catch specific exceptions if possible, but provide a general fallback
        print(f"\nAn unexpected critical error occurred in the application: {e}", file=sys.stderr)
        print("If the problem persists, please check logs or report the issue.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # This allows running the script directly like: python -m stream_manager_cli.main
    # However, the primary execution method after packaging will be via the entry point.
    main()