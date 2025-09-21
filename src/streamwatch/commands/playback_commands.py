"""
Playback-related commands for the StreamWatch application.

This module contains commands that handle stream playback operations such as
playing streams, managing playback sessions, and handling stream navigation.
"""

import logging
from typing import Any, Dict, List, Optional

from .. import config, ui
from .base import Command, CommandResult

logger = logging.getLogger(config.APP_NAME + ".commands.playback_commands")


class PlayStreamCommand(Command):
    """
    Command to play a selected stream.

    This command handles stream selection and delegates playback management
    to the PlaybackController.
    """

    def __init__(
        self,
        live_streams: List[Dict[str, Any]],
        playback_controller: Optional[Any] = None,
        selected_stream: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the PlayStreamCommand.

        Args:
            live_streams: List of currently live streams
            playback_controller: PlaybackController instance for managing playback
            selected_stream: Pre-selected stream (optional, will prompt if None)
        """
        super().__init__("Play Stream")
        self.live_streams = live_streams
        self.playback_controller = playback_controller
        self.selected_stream = selected_stream

    def can_execute(self) -> bool:
        """
        Check if the command can be executed.

        Returns:
            bool: True if there are live streams available, False otherwise
        """
        return len(self.live_streams) > 0

    def execute(self) -> CommandResult:
        """
        Execute the play stream command.

        Prompts user for stream selection (if not pre-selected) and starts playback.

        Returns:
            CommandResult: Result of the play operation
        """
        self.logger.info("Executing play stream command")

        if not self.can_execute():
            return CommandResult(
                success=False,
                message="No live streams available to play.",
                needs_refresh=False,
            )

        try:
            # Get selected stream (either pre-selected or from user input)
            selected_stream_info = self.selected_stream
            if not selected_stream_info:
                selected_stream_info = ui.select_stream_dialog(
                    self.live_streams,
                    title="Select a stream to play",
                    prompt_text="Choose a stream:",
                )

            if not selected_stream_info:
                self.logger.info("Play operation cancelled or no stream selected")
                return CommandResult(
                    success=False,
                    message="Play operation cancelled or no stream selected.",
                    needs_refresh=False,
                )

            # Start playback session
            self.logger.info(f"User selected stream: {selected_stream_info['url']}")

            if not self.playback_controller:
                return CommandResult(
                    success=False,
                    message="Playback controller not available.",
                    needs_refresh=False,
                )

            playback_action = self.playback_controller.start_playback_session(
                selected_stream_info, config.get_streamlink_quality(), self.live_streams
            )

            # Handle playback result
            if playback_action == "quit_application":
                self.logger.info("User quit application from playback session")
                ui.clear_screen()
                ui.console.print("Exiting StreamWatch. Goodbye!", style="success")
                return CommandResult(
                    success=True,
                    message="Application quit requested",
                    needs_refresh=False,
                    should_continue=False,
                )
            elif playback_action == "return_to_main":
                return CommandResult(
                    success=True, message="Returned to main menu", needs_refresh=False
                )
            elif playback_action == "stop_playback":
                return CommandResult(
                    success=True, message="Playback stopped", needs_refresh=False
                )
            elif playback_action == "player_exited":
                return CommandResult(
                    success=True,
                    message="Player exited unexpectedly",
                    needs_refresh=False,
                )
            else:
                return CommandResult(
                    success=True,
                    message="Playback session completed",
                    needs_refresh=False,
                )

        except Exception as e:
            error_msg = f"Error during playback: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class PlayStreamByIndexCommand(Command):
    """
    Command to play a stream by its index in the live streams list.

    This command allows direct selection of a stream by number without
    showing the selection dialog.
    """

    def __init__(
        self,
        stream_index: int,
        live_streams: List[Dict[str, Any]],
        playback_controller: Optional[Any] = None,
    ):
        """
        Initialize the PlayStreamByIndexCommand.

        Args:
            stream_index: Index of the stream to play (0-based)
            live_streams: List of currently live streams
            playback_controller: PlaybackController instance for managing playback
        """
        super().__init__(f"Play Stream #{stream_index + 1}")
        self.stream_index = stream_index
        self.live_streams = live_streams
        self.playback_controller = playback_controller

    def can_execute(self) -> bool:
        """
        Check if the command can be executed.

        Returns:
            bool: True if the stream index is valid, False otherwise
        """
        return len(self.live_streams) > 0 and 0 <= self.stream_index < len(
            self.live_streams
        )

    def execute(self) -> CommandResult:
        """
        Execute the play stream by index command.

        Plays the stream at the specified index.

        Returns:
            CommandResult: Result of the play operation
        """
        self.logger.info(f"Executing play stream by index command: {self.stream_index}")

        if not self.can_execute():
            if len(self.live_streams) == 0:
                return CommandResult(
                    success=False,
                    message="No live streams available to play.",
                    needs_refresh=False,
                )
            else:
                return CommandResult(
                    success=False, message="Invalid stream number.", needs_refresh=False
                )

        try:
            selected_stream_info = self.live_streams[self.stream_index]

            # Create a PlayStreamCommand with the pre-selected stream
            play_command = PlayStreamCommand(
                live_streams=self.live_streams,
                playback_controller=self.playback_controller,
                selected_stream=selected_stream_info,
            )

            return play_command.execute()

        except Exception as e:
            error_msg = f"Error playing stream by index: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


class PlayLastStreamCommand(Command):
    """
    Command to play the last played stream.

    This command attempts to play the stream that was last played by the user,
    checking if it's currently live.
    """

    def __init__(
        self,
        live_streams: List[Dict[str, Any]],
        playback_controller: Optional[Any] = None,
    ):
        """
        Initialize the PlayLastStreamCommand.

        Args:
            live_streams: List of currently live streams
            playback_controller: PlaybackController instance for managing playback
        """
        super().__init__("Play Last Stream")
        self.live_streams = live_streams
        self.playback_controller = playback_controller

    def can_execute(self) -> bool:
        """
        Check if the command can be executed.

        Returns:
            bool: True if there's a last played URL configured, False otherwise
        """
        return config.get_last_played_url() is not None

    def execute(self) -> CommandResult:
        """
        Execute the play last stream command.

        Attempts to find and play the last played stream.

        Returns:
            CommandResult: Result of the play operation
        """
        self.logger.info("Executing play last stream command")

        if not self.can_execute():
            return CommandResult(
                success=False,
                message="No last played stream available.",
                needs_refresh=False,
            )

        try:
            from .. import stream_checker

            last_played_url = config.get_last_played_url()
            self.logger.info(
                f"Attempting to play last played stream: {last_played_url}"
            )

            ui.console.print(
                f"Checking status for last played: [info]{last_played_url}[/info]"
            )

            # Check if last played stream is in current live streams
            found_in_live = next(
                (
                    s_info
                    for s_info in self.live_streams
                    if s_info["url"] == last_played_url
                ),
                None,
            )

            selected_stream_info_for_last_played = None

            if found_in_live:
                self.logger.info("Last played stream found in current live streams")
                selected_stream_info_for_last_played = found_in_live
            else:
                # Check if the stream is live but not in our current list
                self.logger.info(
                    "Last played stream not in current live list, checking status"
                )
                ui.console.print("Stream not in current live list. Checking status...")

                try:
                    # Create a temporary stream info for checking
                    temp_stream_info = {"url": last_played_url}
                    live_check_result = stream_checker.fetch_live_streams(
                        [temp_stream_info]
                    )

                    if live_check_result:
                        self.logger.info("Last played stream is currently live")
                        selected_stream_info_for_last_played = live_check_result[0]
                    else:
                        self.logger.info("Last played stream is not currently live")
                        return CommandResult(
                            success=False,
                            message="Last played stream is not currently live.",
                            needs_refresh=False,
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Error checking last played stream status: {e}"
                    )
                    return CommandResult(
                        success=False,
                        message=f"Error checking last played stream: {str(e)}",
                        needs_refresh=False,
                    )

            if selected_stream_info_for_last_played:
                # Create a PlayStreamCommand with the last played stream
                play_command = PlayStreamCommand(
                    live_streams=self.live_streams,
                    playback_controller=self.playback_controller,
                    selected_stream=selected_stream_info_for_last_played,
                )

                return play_command.execute()
            else:
                return CommandResult(
                    success=False,
                    message="Could not find or verify last played stream.",
                    needs_refresh=False,
                )

        except Exception as e:
            error_msg = f"Error playing last stream: {str(e)}"
            self.logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg, needs_refresh=False)


__all__ = [
    "PlayStreamCommand",
    "PlayStreamByIndexCommand",
    "PlayLastStreamCommand",
]
