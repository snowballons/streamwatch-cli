import logging  # Import logging
import subprocess
import sys
from logging.handlers import RotatingFileHandler  # For log rotation

from . import config  # To get USER_CONFIG_DIR
from . import ui  # For clear_screen
from .app import StreamWatchApp

# from pathlib import Path  # To construct log path


# --- Setup Logging ---
def setup_logging() -> None:
    """Sets up logging configuration for the application."""
    log_dir = config.USER_CONFIG_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "streamwatch.log"

    # Max 1MB per log file, keep 3 backup logs
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    # More detailed format for file logs
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # Log everything DEBUG and above to file

    # Console handler for rich (optional, rich can handle its own console output)
    # If you want to use Python's logging for console as well, styled by rich:
    # from rich.logging import RichHandler
    # console_handler = RichHandler(rich_tracebacks=True, console=ui.console, show_path=False)
    # console_handler.setLevel(logging.INFO) # Log INFO and above to console

    # Get the root logger
    root_logger = logging.getLogger()  # Get root logger
    if (
        not root_logger.handlers
    ):  # Add handlers only if not already configured (e.g. by other imports)
        root_logger.setLevel(logging.DEBUG)  # Set root logger level to lowest (DEBUG)
        root_logger.addHandler(file_handler)
        # root_logger.addHandler(console_handler) # Uncomment if using RichHandler for console

    # Example: Get a logger specific to your app's root package
    # logger = logging.getLogger(config.APP_NAME)
    # if not logger.handlers:
    #     logger.setLevel(logging.DEBUG)
    #     logger.addHandler(file_handler)
    # logger.addHandler(console_handler) # If you want this specific logger to also output to console


def initial_streamlink_check() -> bool:
    """Checks if streamlink command is available and executable."""
    try:
        # Use --version as a lightweight check
        subprocess.run(
            ["streamlink", "--version"], capture_output=True, check=True, timeout=5
        )
        return True
    except FileNotFoundError:
        print("CRITICAL ERROR: streamlink command not found.", file=sys.stderr)
        print(
            "Please ensure streamlink is installed and in your system's PATH.",
            file=sys.stderr,
        )
        return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(
            f"CRITICAL ERROR: streamlink found but is not working correctly: {e}",
            file=sys.stderr,
        )
        return False
    except Exception as e:  # Catch any other unexpected errors
        print(
            f"CRITICAL ERROR: An unexpected issue occurred while checking for streamlink: {e}",
            file=sys.stderr,
        )
        return False


def app() -> None:
    """Main entry point for the StreamWatch CLI application (for script entry point)."""
    main()


def main() -> None:

    setup_logging()
    logger = logging.getLogger(config.APP_NAME)
    logger.info("StreamWatch application started.")

    # --- Automatic Migration from JSON to SQLite ---
    try:
        from .migration import DataMigrator
        migrator = DataMigrator()
        if migrator.check_migration_needed():
            logger.info("Migration needed: starting migration from JSON to SQLite.")
            ui.console.print("[yellow]Migrating your data to the new database format...[/yellow]")
            result = migrator.perform_migration(create_backup=True)
            if result.get("success"):
                ui.console.print(f"[green]Migration completed: {result['streams_migrated']} streams, {result['config_migrated']} config values migrated.[/green]")
                if result.get("backup_path"):
                    ui.console.print(f"[dim]Backup created at: {result['backup_path']}[/dim]")
            else:
                ui.console.print(f"[red]Migration failed: {result['message']}[/red]")
                logger.critical(f"Migration failed: {result['message']}")
                sys.exit(1)
        else:
            logger.info("Migration not needed.")
    except Exception as e:
        logger.critical(f"Migration check/operation failed: {e}", exc_info=True)
        ui.console.print(f"[red]Migration check/operation failed: {e}[/red]")
        sys.exit(1)

    if not initial_streamlink_check():
        logger.critical("Streamlink check failed. Application cannot continue.")
        # ui.console.print(...) already handles user message
        sys.exit(1)

    try:
        # Create and run the StreamWatch application with dependency injection
        app = StreamWatchApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (KeyboardInterrupt).")
        ui.clear_screen()
        ui.console.print(
            "\nScript interrupted by user. Exiting gracefully. Goodbye!", style="info"
        )
if __name__ == "__main__":
    # This allows running the script directly like: python -m stream_manager_cli.main
    # However, the primary execution method after packaging will be via the entry point.
    main()
