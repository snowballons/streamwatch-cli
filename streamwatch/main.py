import subprocess
import sys
import logging # Import logging
from logging.handlers import RotatingFileHandler # For log rotation
from pathlib import Path # To construct log path

from . import core
from . import ui # For clear_screen
from . import config # To get USER_CONFIG_DIR

# --- Setup Logging ---
def setup_logging():
    log_dir = config.USER_CONFIG_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "streamwatch.log"

    # Max 1MB per log file, keep 3 backup logs
    file_handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=3, encoding='utf-8')
    # More detailed format for file logs
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG) # Log everything DEBUG and above to file

    # Console handler for rich (optional, rich can handle its own console output)
    # If you want to use Python's logging for console as well, styled by rich:
    # from rich.logging import RichHandler
    # console_handler = RichHandler(rich_tracebacks=True, console=ui.console, show_path=False)
    # console_handler.setLevel(logging.INFO) # Log INFO and above to console

    # Get the root logger
    root_logger = logging.getLogger() # Get root logger
    if not root_logger.handlers: # Add handlers only if not already configured (e.g. by other imports)
        root_logger.setLevel(logging.DEBUG) # Set root logger level to lowest (DEBUG)
        root_logger.addHandler(file_handler)
        # root_logger.addHandler(console_handler) # Uncomment if using RichHandler for console

    # Example: Get a logger specific to your app's root package
    # logger = logging.getLogger(config.APP_NAME)
    # if not logger.handlers:
    #     logger.setLevel(logging.DEBUG)
    #     logger.addHandler(file_handler)
        # logger.addHandler(console_handler) # If you want this specific logger to also output to console

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
    """Entry point for the StreamWatch CLI application."""
    setup_logging() # <<<<<<<<<<<<<<<<<<<<<<<< ADD THIS
    logger = logging.getLogger(config.APP_NAME) # Get a named logger
    logger.info("StreamWatch application started.")

    if not initial_streamlink_check():
        logger.critical("Streamlink check failed. Application cannot continue.")
        # ui.console.print(...) already handles user message
        sys.exit(1)

    try:
        core.run_interactive_loop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (KeyboardInterrupt).")
        ui.clear_screen()
        ui.console.print("\nScript interrupted by user. Exiting gracefully. Goodbye!", style="info")
    except Exception as e:
        logger.critical("An unexpected critical error occurred in the application.", exc_info=True)
        ui.clear_screen()
        ui.console.print(f"\n[error]An unexpected critical error occurred: {e}[/error]", style="error")
        ui.console.print("Please check the log file for more details.", style="dimmed")
        ui.console.print(f"Log file location: {config.USER_CONFIG_DIR / 'logs' / 'streamwatch.log'}", style="dimmed")
        sys.exit(1)
    logger.info("StreamWatch application finished.")

if __name__ == '__main__':
    # This allows running the script directly like: python -m stream_manager_cli.main
    # However, the primary execution method after packaging will be via the entry point.
    main()