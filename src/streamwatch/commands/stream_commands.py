"""
Stream-related commands for the StreamWatch application.

This module contains commands that handle stream operations such as adding,
removing, listing, importing, and exporting streams.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, ui
from .base import Command, CommandResult

logger = logging.getLogger(config.APP_NAME + ".commands.stream_commands")


class AddStreamCommand(Command):
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

    def execute(self) -> CommandResult:
        """Executes the add stream command by delegating to the StreamManager."""
        self.logger.info("Delegating add stream execution to StreamManager")
        success, message = self.stream_manager.add_streams()
        # We can't easily undo this now, so we'll simplify the command
        return CommandResult(success=success, message=message, needs_refresh=success)




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
        """Executes the remove stream command by delegating to the StreamManager."""
        self.logger.info("Delegating remove stream execution to StreamManager")
        success, message = self.stream_manager.remove_streams()
        return CommandResult(success=success, message=message, needs_refresh=success)


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
        """Executes the list streams command by delegating to the StreamManager."""
        self.logger.info("Delegating list streams execution to StreamManager")
        self.stream_manager.list_streams()
        return CommandResult(success=True, message="Streams listed.")


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
        """Executes the import streams command by delegating to the StreamManager."""
        self.logger.info("Delegating import streams execution to StreamManager")
        success, message = self.stream_manager.import_streams()
        return CommandResult(success=success, message=message, needs_refresh=success)


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
        """Executes the export streams command by delegating to the StreamManager."""
        self.logger.info("Delegating export streams execution to StreamManager")
        success, message = self.stream_manager.export_streams()
        return CommandResult(success=success, message=message)


__all__ = [
    "AddStreamCommand",
    "RemoveStreamCommand",
    "ListStreamsCommand",
    "RefreshStreamsCommand",
    "ImportStreamsCommand",
    "ExportStreamsCommand",
]
