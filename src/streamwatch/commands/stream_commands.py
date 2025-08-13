"""
Stream-related commands for the StreamWatch application.

This module contains commands that handle stream operations such as adding,
removing, listing, importing, and exporting streams.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, storage, ui
from .base import Command, CommandResult, UndoableCommand

logger = logging.getLogger(config.APP_NAME + ".commands.stream_commands")


class AddStreamCommand(UndoableCommand):
    """
    Command to add new streams to the StreamWatch configuration.

    This command handles the user interaction for adding streams and
    delegates the actual storage operation to the storage module.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the AddStreamCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("Add Stream")
        self.stream_manager = stream_manager
        self.added_streams: List[Dict[str, str]] = []

    def execute(self) -> CommandResult:
        """
        Execute the add stream command.

        Prompts the user for stream URLs and aliases, then adds them to storage.

        Returns:
            CommandResult: Result of the add operation
        """
        self.logger.info("Executing add stream command")

        try:
            # Get new streams from user input
            new_streams_to_add = ui.prompt_add_streams()

            if not new_streams_to_add:
                self.logger.info("Add operation cancelled or no URLs entered")
                return CommandResult(
                    success=False,
                    message="Add operation cancelled or no URLs entered.",
                    needs_refresh=False,
                )

            # Store the streams for potential undo
            self.added_streams = new_streams_to_add.copy()

            # Add streams to storage
            success, message = storage.add_streams(new_streams_to_add)

            if success:
                self.logger.info("Streams added successfully")
                return CommandResult(success=True, message=message, needs_refresh=True)
            else:
                self.logger.warning(f"Failed to add streams: {message}")
                return CommandResult(
                    success=False, message=message, needs_refresh=False
                )

        except Exception as e:
            error_msg = f"Error adding streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)

    def undo(self) -> CommandResult:
        """
        Undo the add stream command by removing the added streams.

        Returns:
            CommandResult: Result of the undo operation
        """
        if not self.added_streams:
            return CommandResult(
                success=False, message="No streams to undo", needs_refresh=False
            )

        try:
            # Load current streams and find indices of added streams
            current_streams = storage.load_streams()
            indices_to_remove = []

            for added_stream in self.added_streams:
                for i, stream in enumerate(current_streams):
                    if stream.get("url") == added_stream.get("url"):
                        indices_to_remove.append(i)
                        break

            if indices_to_remove:
                success, message = storage.remove_streams_by_indices(indices_to_remove)
                if success:
                    self.logger.info("Successfully undid add stream command")
                    return CommandResult(
                        success=True,
                        message=f"Undid add operation: {message}",
                        needs_refresh=True,
                    )
                else:
                    return CommandResult(
                        success=False,
                        message=f"Failed to undo add operation: {message}",
                        needs_refresh=False,
                    )
            else:
                return CommandResult(
                    success=False,
                    message="Could not find added streams to remove",
                    needs_refresh=False,
                )

        except Exception as e:
            error_msg = f"Error undoing add streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class RemoveStreamCommand(Command):
    """
    Command to remove streams from the StreamWatch configuration.

    This command handles the user interaction for removing streams and
    delegates the actual storage operation to the storage module.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the RemoveStreamCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("Remove Stream")
        self.stream_manager = stream_manager

    def execute(self) -> CommandResult:
        """
        Execute the remove stream command.

        Shows the user available streams and prompts for removal selection.

        Returns:
            CommandResult: Result of the remove operation
        """
        self.logger.info("Executing remove stream command")

        try:
            # Load current streams
            current_all_streams = storage.load_streams()

            if not current_all_streams:
                return CommandResult(
                    success=False,
                    message="No streams available to remove.",
                    needs_refresh=False,
                )

            # Get user selection for removal
            indices_to_remove = ui.prompt_remove_streams_dialog(current_all_streams)

            if indices_to_remove is None:  # Explicit cancel from dialog
                self.logger.info("Remove operation cancelled")
                return CommandResult(
                    success=False,
                    message="Remove operation cancelled.",
                    needs_refresh=False,
                )
            elif not indices_to_remove:  # Empty list returned
                self.logger.info("No valid streams selected for removal")
                return CommandResult(
                    success=False,
                    message="No valid streams selected for removal.",
                    needs_refresh=False,
                )

            # Remove streams from storage
            success, message = storage.remove_streams_by_indices(indices_to_remove)

            if success:
                self.logger.info("Streams removed successfully")
                return CommandResult(success=True, message=message, needs_refresh=True)
            else:
                self.logger.warning(f"Failed to remove streams: {message}")
                return CommandResult(
                    success=False, message=message, needs_refresh=False
                )

        except Exception as e:
            error_msg = f"Error removing streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class ListStreamsCommand(Command):
    """
    Command to list all configured streams.

    This command displays all streams in the configuration without
    modifying any data.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the ListStreamsCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("List Streams")
        self.stream_manager = stream_manager

    def execute(self) -> CommandResult:
        """
        Execute the list streams command.

        Displays all configured streams to the user.

        Returns:
            CommandResult: Result of the list operation
        """
        self.logger.info("Executing list streams command")

        try:
            # Clear screen and load streams
            ui.clear_screen()
            current_all_stream_urls = storage.load_streams()

            # Display streams
            ui.display_stream_list(
                current_all_stream_urls, title="--- All Configured Streams ---"
            )
            ui.show_message("", duration=0, pause_after=True)

            return CommandResult(
                success=True, message="Streams listed successfully", needs_refresh=False
            )

        except Exception as e:
            error_msg = f"Error listing streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class RefreshStreamsCommand(Command):
    """
    Command to refresh the status of all configured streams.

    This command triggers a refresh of the live stream status without
    modifying any configuration data.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the RefreshStreamsCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("Refresh Streams")
        self.stream_manager = stream_manager

    def execute(self) -> CommandResult:
        """
        Execute the refresh streams command.

        Triggers a refresh of the live stream status.

        Returns:
            CommandResult: Result of the refresh operation
        """
        self.logger.info("Executing refresh streams command")

        try:
            # The refresh operation is typically handled by the main loop
            # This command just signals that a refresh is needed
            return CommandResult(
                success=True, message="Stream list refreshed", needs_refresh=True
            )

        except Exception as e:
            error_msg = f"Error refreshing streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class ImportStreamsCommand(Command):
    """
    Command to import streams from a text file.

    This command handles the user interaction for importing streams from
    an external file and delegates the actual import operation to the storage module.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the ImportStreamsCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("Import Streams")
        self.stream_manager = stream_manager

    def execute(self) -> CommandResult:
        """
        Execute the import streams command.

        Prompts user for file path and imports streams from the specified file.

        Returns:
            CommandResult: Result of the import operation
        """
        self.logger.info("Executing import streams command")

        try:
            # Get file path from user
            filepath = ui.prompt_for_filepath(
                "Enter path of .txt file to import from: "
            )

            if not filepath:
                self.logger.info("Import operation cancelled")
                return CommandResult(
                    success=False, message="Import cancelled.", needs_refresh=False
                )

            # Import streams from file
            success, message = storage.import_streams_from_txt(Path(filepath))

            if success:
                self.logger.info("Streams imported successfully")
                return CommandResult(success=True, message=message, needs_refresh=True)
            else:
                self.logger.warning(f"Failed to import streams: {message}")
                return CommandResult(
                    success=False, message=message, needs_refresh=False
                )

        except Exception as e:
            error_msg = f"Error importing streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class ExportStreamsCommand(Command):
    """
    Command to export streams to a JSON file.

    This command handles the user interaction for exporting streams to
    an external file and delegates the actual export operation to the storage module.
    """

    def __init__(self, stream_manager: Optional[Any] = None):
        """
        Initialize the ExportStreamsCommand.

        Args:
            stream_manager: Optional StreamManager instance for dependency injection
        """
        super().__init__("Export Streams")
        self.stream_manager = stream_manager

    def execute(self) -> CommandResult:
        """
        Execute the export streams command.

        Prompts user for file path and exports streams to the specified file.

        Returns:
            CommandResult: Result of the export operation
        """
        self.logger.info("Executing export streams command")

        try:
            import time

            # Generate default export path
            default_export_path = (
                f"~/streamwatch_export_{time.strftime('%Y-%m-%d')}.json"
            )

            # Get file path from user
            filepath = ui.prompt_for_filepath(
                "Enter path to save export file: ", default_filename=default_export_path
            )

            if not filepath:
                self.logger.info("Export operation cancelled")
                return CommandResult(
                    success=False, message="Export cancelled.", needs_refresh=False
                )

            # Export streams to file
            success, message = storage.export_streams_to_json(Path(filepath))

            if success:
                self.logger.info("Streams exported successfully")
                return CommandResult(success=True, message=message, needs_refresh=False)
            else:
                self.logger.warning(f"Failed to export streams: {message}")
                return CommandResult(
                    success=False, message=message, needs_refresh=False
                )

        except Exception as e:
            error_msg = f"Error exporting streams: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


__all__ = [
    "AddStreamCommand",
    "RemoveStreamCommand",
    "ListStreamsCommand",
    "RefreshStreamsCommand",
    "ImportStreamsCommand",
    "ExportStreamsCommand",
]
