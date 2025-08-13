"""
Base Command classes for the StreamWatch Command Pattern implementation.

This module defines the abstract base classes and interfaces for the Command Pattern,
allowing operations to be encapsulated as objects for better separation of concerns,
undo functionality, and command queuing.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .. import config

logger = logging.getLogger(config.APP_NAME + ".commands.base")


class CommandResult:
    """
    Represents the result of a command execution.

    This class encapsulates the outcome of a command, including success status,
    messages, and any additional data that might be needed by the caller.
    """

    def __init__(
        self,
        success: bool,
        message: str = "",
        needs_refresh: bool = False,
        should_continue: bool = True,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a CommandResult.

        Args:
            success: Whether the command executed successfully
            message: Optional message describing the result
            needs_refresh: Whether the UI needs to refresh after this command
            should_continue: Whether the application should continue running
            data: Optional additional data from the command execution
        """
        self.success = success
        self.message = message
        self.needs_refresh = needs_refresh
        self.should_continue = should_continue
        self.data = data or {}

    def __str__(self) -> str:
        """String representation of the command result."""
        return f"CommandResult(success={self.success}, message='{self.message}')"


class Command(ABC):
    """
    Abstract base class for all commands in the StreamWatch application.

    This class defines the interface that all concrete commands must implement.
    Commands encapsulate a specific operation and can be executed, providing
    a consistent interface for different types of operations.
    """

    def __init__(self, name: str):
        """
        Initialize a Command.

        Args:
            name: Human-readable name for this command
        """
        self.name = name
        self.logger = logging.getLogger(
            f"{config.APP_NAME}.commands.{self.__class__.__name__}"
        )

    @abstractmethod
    def execute(self) -> CommandResult:
        """
        Execute the command.

        This method must be implemented by all concrete command classes.
        It should perform the command's operation and return a CommandResult
        indicating the outcome.

        Returns:
            CommandResult: The result of the command execution
        """
        pass

    def can_execute(self) -> bool:
        """
        Check if the command can be executed.

        This method can be overridden by concrete commands to implement
        precondition checks. By default, all commands can be executed.

        Returns:
            bool: True if the command can be executed, False otherwise
        """
        return True

    def __str__(self) -> str:
        """String representation of the command."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class UndoableCommand(Command):
    """
    Abstract base class for commands that can be undone.

    This class extends the basic Command interface to support undo operations,
    allowing for more sophisticated command management and user experience.
    """

    @abstractmethod
    def undo(self) -> CommandResult:
        """
        Undo the command.

        This method must be implemented by concrete undoable command classes.
        It should reverse the effects of the execute() method.

        Returns:
            CommandResult: The result of the undo operation
        """
        pass

    def can_undo(self) -> bool:
        """
        Check if the command can be undone.

        This method can be overridden by concrete commands to implement
        undo precondition checks. By default, all undoable commands can be undone.

        Returns:
            bool: True if the command can be undone, False otherwise
        """
        return True


__all__ = [
    "Command",
    "UndoableCommand",
    "CommandResult",
]
