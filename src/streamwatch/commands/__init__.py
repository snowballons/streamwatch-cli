"""
StreamWatch Commands Package

This package implements the Command Pattern for StreamWatch operations.
Commands encapsulate operations as objects, allowing for better separation of concerns,
undo functionality, and command queuing.
"""

# Import base classes
from .base import Command, CommandResult

# Import command invoker
from .invoker import CommandInvoker

# Import playback-related commands
from .playback_commands import (
    PlayLastStreamCommand,
    PlayStreamByIndexCommand,
    PlayStreamCommand,
)

# Import recording-related commands
from .recording_commands import (
    ListRecordingsCommand,
    StartRecordingCommand,
    StopAllRecordingsCommand,
    StopRecordingCommand,
)

# Import stream-related commands
from .stream_commands import (
    AddStreamCommand,
    ExportStreamsCommand,
    ImportStreamsCommand,
    ListStreamsCommand,
    RefreshStreamsCommand,
    RemoveStreamCommand,
)

__all__ = [
    # Base classes
    "Command",
    "CommandResult",
    # Command invoker
    "CommandInvoker",
    # Recording commands
    "StartRecordingCommand",
    "StopRecordingCommand",
    "ListRecordingsCommand",
    "StopAllRecordingsCommand",
    # Stream commands
    "AddStreamCommand",
    "RemoveStreamCommand",
    "ListStreamsCommand",
    "RefreshStreamsCommand",
    "ImportStreamsCommand",
    "ExportStreamsCommand",
    # Playback commands
    "PlayStreamCommand",
    "PlayStreamByIndexCommand",
    "PlayLastStreamCommand",
]
