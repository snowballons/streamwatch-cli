"""
Command Invoker for the StreamWatch Command Pattern implementation.

This module contains the CommandInvoker class that manages command execution,
history, and provides undo functionality for commands that support it.
"""

import logging
from typing import Any, Dict, List, Optional

from .. import config
from .base import Command, CommandResult, UndoableCommand

logger = logging.getLogger(config.APP_NAME + ".commands.invoker")


class CommandInvoker:
    """
    Manages command execution and history for the StreamWatch application.

    The CommandInvoker is responsible for executing commands, maintaining
    a history of executed commands, and providing undo functionality for
    commands that support it.
    """

    def __init__(self, max_history_size: int = 50):
        """
        Initialize the CommandInvoker.

        Args:
            max_history_size: Maximum number of commands to keep in history
        """
        self.max_history_size = max_history_size
        self.command_history: List[Command] = []
        self.undo_stack: List[UndoableCommand] = []
        self.logger = logging.getLogger(f"{config.APP_NAME}.commands.invoker")

    def execute_command(self, command: Command) -> CommandResult:
        """
        Execute a command and manage its history.

        Args:
            command: The command to execute

        Returns:
            CommandResult: The result of the command execution
        """
        self.logger.info(f"Executing command: {command}")

        # Check if command can be executed
        if not command.can_execute():
            self.logger.warning(f"Command cannot be executed: {command}")
            return CommandResult(
                success=False,
                message=f"Command '{command.name}' cannot be executed.",
                needs_refresh=False,
            )

        try:
            # Execute the command
            result = command.execute()

            # Add to history if execution was successful
            if result.success:
                self._add_to_history(command)

                # Add to undo stack if it's an undoable command
                if isinstance(command, UndoableCommand):
                    self._add_to_undo_stack(command)

            self.logger.info(f"Command executed: {command} - Result: {result}")
            return result

        except Exception as e:
            error_msg = f"Error executing command {command}: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)

    def undo_last_command(self) -> CommandResult:
        """
        Undo the last undoable command.

        Returns:
            CommandResult: The result of the undo operation
        """
        if not self.undo_stack:
            self.logger.info("No commands available to undo")
            return CommandResult(
                success=False,
                message="No commands available to undo.",
                needs_refresh=False,
            )

        last_command = self.undo_stack[-1]
        self.logger.info(f"Undoing command: {last_command}")

        # Check if command can be undone
        if not last_command.can_undo():
            self.logger.warning(f"Command cannot be undone: {last_command}")
            return CommandResult(
                success=False,
                message=f"Command '{last_command.name}' cannot be undone.",
                needs_refresh=False,
            )

        try:
            # Undo the command
            result = last_command.undo()

            # Remove from undo stack if undo was successful
            if result.success:
                self.undo_stack.pop()

            self.logger.info(f"Command undone: {last_command} - Result: {result}")
            return result

        except Exception as e:
            error_msg = f"Error undoing command {last_command}: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)

    def get_command_history(self) -> List[Command]:
        """
        Get the command execution history.

        Returns:
            List[Command]: List of executed commands in chronological order
        """
        return self.command_history.copy()

    def get_undo_stack(self) -> List[UndoableCommand]:
        """
        Get the undo stack.

        Returns:
            List[UndoableCommand]: List of undoable commands in reverse chronological order
        """
        return self.undo_stack.copy()

    def clear_history(self) -> None:
        """Clear the command history and undo stack."""
        self.logger.info("Clearing command history and undo stack")
        self.command_history.clear()
        self.undo_stack.clear()

    def can_undo(self) -> bool:
        """
        Check if there are commands that can be undone.

        Returns:
            bool: True if there are undoable commands, False otherwise
        """
        return (len(self.undo_stack) > 0 and
                self.undo_stack[-1].can_undo())

    def get_last_command(self) -> Optional[Command]:
        """
        Get the last executed command.

        Returns:
            Optional[Command]: The last executed command, or None if no commands have been executed
        """
        return (self.command_history[-1] if self.command_history
                else None)

    def get_last_undoable_command(self) -> Optional[UndoableCommand]:
        """
        Get the last undoable command.

        Returns:
            Optional[UndoableCommand]: The last undoable command, or None if no undoable commands exist
        """
        return (self.undo_stack[-1] if self.undo_stack
                else None)

    def _add_to_history(self, command: Command) -> None:
        """
        Add a command to the execution history.

        Args:
            command: The command to add to history
        """
        self.command_history.append(command)

        # Maintain maximum history size
        if len(self.command_history) > self.max_history_size:
            self.command_history.pop(0)

    def _add_to_undo_stack(self, command: UndoableCommand) -> None:
        """
        Add an undoable command to the undo stack.

        Args:
            command: The undoable command to add to the undo stack
        """
        self.undo_stack.append(command)

        # Maintain reasonable undo stack size (smaller than history)
        max_undo_size = min(self.max_history_size // 2, 25)
        if len(self.undo_stack) > max_undo_size:
            self.undo_stack.pop(0)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about command execution.

        Returns:
            Dict[str, Any]: Statistics about command history and undo stack
        """
        return {
            "total_commands_executed": len(self.command_history),
            "undoable_commands_available": len(self.undo_stack),
            "can_undo": self.can_undo(),
            "last_command": str(self.get_last_command())
            if self.get_last_command()
            else None,
            "last_undoable_command": str(self.get_last_undoable_command())
            if self.get_last_undoable_command()
            else None,
        }

    def __str__(self) -> str:
        """String representation of the CommandInvoker."""
        stats = self.get_statistics()
        return f"CommandInvoker(executed={stats['total_commands_executed']}, undoable={stats['undoable_commands_available']})"


__all__ = [
    "CommandInvoker",
]
