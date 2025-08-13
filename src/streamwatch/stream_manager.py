"""Stream management functionality for StreamWatch application."""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import config, storage, ui

logger = logging.getLogger(config.APP_NAME + ".stream_manager")


class StreamManager:
    """Handles stream CRUD operations for the StreamWatch application."""

    def __init__(self):
        """Initialize the StreamManager."""
        pass

    def add_streams(self) -> Tuple[bool, str]:
        """
        Handle adding new streams through user interface.

        Returns:
            Tuple of (success_bool, message_str)
        """
        new_urls_to_add = ui.prompt_add_streams()
        if new_urls_to_add:
            success, message = storage.add_streams(new_urls_to_add)
            if success:
                logger.info("Streams added successfully.")
            return success, message
        else:
            logger.info("Add operation cancelled or no URLs entered.")
            return False, "Add operation cancelled or no URLs entered."

    def remove_streams(self) -> Tuple[bool, str]:
        """
        Handle removing streams through user interface.

        Returns:
            Tuple of (success_bool, message_str)
        """
        current_all_streams = storage.load_streams()
        indices_to_remove = ui.prompt_remove_streams_dialog(current_all_streams)

        if indices_to_remove is not None and indices_to_remove:
            success, message = storage.remove_streams_by_indices(indices_to_remove)
            if success:
                logger.info("Streams removed successfully.")
            return success, message
        elif indices_to_remove is None:  # Explicit cancel from dialog
            logger.info("Remove operation cancelled.")
            return False, "Remove operation cancelled."
        else:  # Empty list returned
            if current_all_streams:
                logger.info("No valid streams selected for removal.")
                return False, "No valid streams selected for removal."
            return False, "No streams available to remove."

    def list_streams(self) -> None:
        """Display all configured streams."""
        ui.clear_screen()
        current_all_stream_urls = storage.load_streams()
        ui.display_stream_list(
            current_all_stream_urls, title="--- All Configured Streams ---"
        )
        ui.show_message("", duration=0, pause_after=True)

    def import_streams(self) -> Tuple[bool, str]:
        """
        Handle importing streams from a file through user interface.

        Returns:
            Tuple of (success_bool, message_str)
        """
        filepath = ui.prompt_for_filepath("Enter path of .txt file to import from: ")
        if filepath:
            success, message = storage.import_streams_from_txt(Path(filepath))
            return success, message
        else:
            return False, "Import cancelled."

    def export_streams(self) -> Tuple[bool, str]:
        """
        Handle exporting streams to a file through user interface.

        Returns:
            Tuple of (success_bool, message_str)
        """
        default_export_path = f"~/streamwatch_export_{time.strftime('%Y-%m-%d')}.json"
        filepath = ui.prompt_for_filepath(
            "Enter path to save export file: ", default_filename=default_export_path
        )
        if filepath:
            success, message = storage.export_streams_to_json(Path(filepath))
            return success, message
        else:
            return False, "Export cancelled."

    def load_streams(self) -> List[Dict[str, Any]]:
        """
        Load all configured streams.

        Returns:
            List of stream dictionaries
        """
        return storage.load_streams()

    def get_stream_count(self) -> int:
        """
        Get the total number of configured streams.

        Returns:
            Number of configured streams
        """
        return len(storage.load_streams())
