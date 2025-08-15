import logging
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import config, ui
from .database import StreamDatabase
from .models import StreamInfo
from .stream_utils import parse_url_metadata

logger = logging.getLogger(config.APP_NAME + ".stream_manager")


class StreamManager:
    """Handles stream CRUD operations for the StreamWatch application."""

    def __init__(self, database: StreamDatabase):
        """Initialize the StreamManager with a database dependency."""
        self.db = database

    def add_streams(self) -> Tuple[bool, str]:
        """Handle adding new streams to the database via the UI."""
        new_streams_data = ui.prompt_add_streams()
        if not new_streams_data:
            logger.info("Add operation cancelled or no URLs entered.")
            return False, "Add operation cancelled or no URLs entered."

        added_count = 0
        for stream_data in new_streams_data:
            try:
                url = stream_data['url']
                alias = stream_data['alias']

                # Parse the URL to get platform and a default username
                parsed_info = parse_url_metadata(url)
                platform = parsed_info.get('platform', 'Unknown')
                username = parsed_info.get('username', 'unknown_stream')

                # If no alias was provided by the user, use the username as the default
                if not alias:
                    alias = username

                # Create a complete, validated StreamInfo object
                stream = StreamInfo(url=url, alias=alias, platform=platform, username=username)
                self.db.save_stream(stream)
                added_count += 1
            except Exception as e:
                logger.warning(f"Could not add stream {stream_data.get('url')}: {e}")
                ui.console.print(f"[error]Failed to add stream '{stream_data.get('url')}': {e}[/error]")
        
        if added_count > 0:
            message = f"Successfully added {added_count} new stream(s)."
            return True, message
        else:
            return False, "No new streams were added."

    def remove_streams(self) -> Tuple[bool, str]:
        """Handle removing streams from the database via the UI."""
        all_streams = self.db.load_streams()
        all_streams_dicts = [s.model_dump() for s in all_streams]

        indices_to_remove = ui.prompt_remove_streams_dialog(all_streams_dicts)

        if indices_to_remove is not None and indices_to_remove:
            removed_count = 0
            for index in indices_to_remove:
                if 0 <= index < len(all_streams):
                    stream_to_remove = all_streams[index]
                    if self.db.delete_stream(stream_to_remove.url):
                        removed_count += 1
            
            message = f"Successfully removed {removed_count} stream(s)."
            return True, message
        elif indices_to_remove is None:
            return False, "Remove operation cancelled."
        else:
            return False, "No valid streams selected for removal."

    def list_streams(self) -> None:
        """Display all configured streams from the database."""
        ui.clear_screen()
        all_streams = self.db.load_streams()
        all_streams_dicts = [s.model_dump() for s in all_streams]
        ui.display_stream_list(
            all_streams_dicts, title="--- All Configured Streams ---"
        )
        ui.show_message("", duration=0, pause_after=True)

    def import_streams(self) -> Tuple[bool, str]:
        """Handle importing streams from a file into the database."""
        filepath_str = ui.prompt_for_filepath("Enter path of .txt file to import from: ")
        if not filepath_str:
            return False, "Import cancelled."

        try:
            source_path = Path(filepath_str).expanduser()
            if not source_path.is_file():
                return False, f"Import file not found at: {source_path}"

            with open(source_path, 'r', encoding='utf-8') as f:
                urls_to_import = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            if not urls_to_import:
                return False, "Import file is empty or contains no valid lines."

            imported_count = 0
            for url in urls_to_import:
                try:
                    parsed_info = parse_url_metadata(url)
                    platform = parsed_info.get('platform', 'Unknown')
                    username = parsed_info.get('username', 'unknown_stream')
                    alias = username  # For imports, the username is the best default alias

                    stream_info = StreamInfo(url=url, alias=alias, platform=platform, username=username)
                    self.db.save_stream(stream_info)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Could not import stream URL {url}: {e}")
            
            message = f"Successfully imported {imported_count} stream(s)."
            return True, message
        except Exception as e:
            message = f"An error occurred during import: {e}"
            logger.error(message, exc_info=True)
            return False, message

    def export_streams(self) -> Tuple[bool, str]:
        """Handle exporting streams from the database to a JSON file."""
        default_export_path = f"~/streamwatch_export_{time.strftime('%Y-%m-%d')}.json"
        filepath_str = ui.prompt_for_filepath(
            "Enter path to save export file: ", default_filename=default_export_path
        )
        if not filepath_str:
            return False, "Export cancelled."

        try:
            destination_path = Path(filepath_str).expanduser()
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            all_streams = self.db.load_streams()
            if not all_streams:
                return False, "There are no streams in the database to export."

            streams_to_export = [s.model_dump(mode='json') for s in all_streams]

            with open(destination_path, 'w', encoding='utf-8') as f:
                json.dump(streams_to_export, f, indent=4)
            
            message = f"Successfully exported {len(all_streams)} streams to {destination_path}"
            logger.info(message)
            return True, message
        except Exception as e:
            message = f"An error occurred during export: {e}"
            logger.error(message, exc_info=True)
            return False, message

    def load_streams(self) -> List[Dict[str, Any]]:
        """Load all streams from the database and returns them as dicts."""
        all_streams = self.db.load_streams()
        return [s.model_dump() for s in all_streams]

    def get_stream_count(self) -> int:
        """Get the total number of configured streams from the database."""
        return len(self.db.load_streams())