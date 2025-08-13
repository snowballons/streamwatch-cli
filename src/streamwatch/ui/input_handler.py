"""
StreamWatch UI Input Handler Module

This module contains all input handling and user interaction functions for the StreamWatch CLI application.
It handles prompts, dialogs, and user input processing.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import message_dialog, radiolist_dialog
from rich.text import Text

from .. import config
from .display import clear_screen, format_stream_for_display
from .styles import console, dialog_style, playback_menu_style

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".ui.input_handler")


def prompt_for_filepath(
    prompt_text: str = "Enter file path: ", default_filename: str = ""
) -> Optional[str]:
    """Prompts the user to enter a file path."""
    console.print(
        "Enter the path for the file. You can use `~` for your home directory."
    )
    console.print("Press Ctrl+D or Ctrl+C to cancel.", style="dimmed")
    try:
        # prompt_toolkit's prompt has a `default` argument
        filepath = prompt(prompt_text, default=default_filename, style=dialog_style)
        return str(filepath).strip() if filepath else None
    except (EOFError, KeyboardInterrupt):
        console.print("\nOperation cancelled.", style="warning")
        return None


def select_stream_dialog(
    stream_info_list: List[Dict[str, Any]],
    title: str = "Select a stream to play",
    prompt_text: str = "Choose a stream:",
) -> Optional[Dict[str, Any]]:
    """Displays an interactive dialog to select a stream."""
    if not stream_info_list:
        message_dialog(
            title="No Streams",
            text="There are no streams available to select.",
            style=dialog_style,
        ).run()
        return None

    choices = []
    for i, s_info in enumerate(stream_info_list):
        display_text_str = str(
            format_stream_for_display(s_info, index=i, for_prompt_toolkit=True)
        )
        choices.append((s_info, display_text_str))

    rich_prompt_text = Text()
    rich_prompt_text.append(prompt_text + "\n")
    rich_prompt_text.append("(Use ", style="dimmed")
    rich_prompt_text.append("↑↓ arrows", style="bold cyan")
    rich_prompt_text.append(", ", style="dimmed")
    rich_prompt_text.append("number", style="bold cyan")
    rich_prompt_text.append(", or ", style="dimmed")
    rich_prompt_text.append("first letter", style="bold cyan")
    rich_prompt_text.append(". ", style="dimmed")
    rich_prompt_text.append("Enter", style="bold green")
    rich_prompt_text.append(" to select, ", style="dimmed")
    rich_prompt_text.append("Esc/Ctrl+C", style="bold red")
    rich_prompt_text.append(" to cancel)", style="dimmed")

    selected_stream_info = radiolist_dialog(
        title=title, text=str(rich_prompt_text), values=choices, style=dialog_style
    ).run()
    return selected_stream_info


def prompt_add_streams() -> List[Dict[str, str]]:
    """Prompts the user for URLs and optional aliases."""
    clear_screen()
    console.print("--- Add New Stream(s) ---", style="title")
    console.print(
        "Enter stream URL(s). You can provide an optional alias after the URL with a space."
    )
    console.print("Example: [cyan]https://twitch.tv/shroud My Favorite FPS[/cyan]")
    console.print(
        "Example (multiple): [cyan]https://youtube.com/@LTT, https://twitch.tv/pokimane Queen Poki[/cyan]"
    )
    console.print("Press Ctrl+D or Ctrl+C to cancel.", style="dimmed")

    try:
        urls_input = prompt("URL(s) [and optional alias(es)]: ", style=dialog_style)
        if not urls_input:
            return []

        new_streams_data = []
        # Split by comma first to handle multiple entries
        entries = urls_input.split(",")
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split(maxsplit=1)  # Split only on the first space
            url = parts[0]
            alias = parts[1] if len(parts) > 1 else ""
            new_streams_data.append({"url": url.strip(), "alias": alias.strip()})

        return new_streams_data
    except (EOFError, KeyboardInterrupt):
        console.print("\nAdd operation cancelled.", style="warning")
        return []


def prompt_remove_streams_dialog(
    all_streams_data: List[Dict[str, Any]], title: str = "Select streams to REMOVE"
) -> Optional[List[int]]:
    """Now displays alias and URL for easier identification."""
    if not all_streams_data:
        message_dialog(
            title="No Streams",
            text="There are no configured streams to remove.",
            style=dialog_style,
        ).run()
        return None

    clear_screen()
    console.print("--- Remove Configured Stream(s) ---", style="title")
    for i, s_data in enumerate(all_streams_data):
        console.print(
            f"  [{i+1}] [highlight]{s_data.get('alias', s_data.get('url'))}[/highlight] [dim]({s_data.get('url')})[/dim]"
        )

    console.print("\nEnter the number(s) of the stream(s) you want to remove.")
    console.print(
        "Multiple numbers separated by spaces or commas (e.g., 1 3 4 or 1,3,4).",
        style="dimmed",
    )
    console.print(
        "Press Ctrl+D or Ctrl+C (or Esc then Enter on Windows) to cancel.",
        style="dimmed",
    )

    try:
        choice_input = prompt("Remove number(s): ", style=dialog_style)
        if not choice_input:
            return []
    except (EOFError, KeyboardInterrupt):
        console.print("\nRemove operation cancelled.", style="warning")
        return []

    try:
        raw_indices_str = choice_input.replace(",", " ").split()
        indices_to_remove = []
        invalid_inputs = []
        for s_idx_str in raw_indices_str:
            s_idx_str = s_idx_str.strip()
            if s_idx_str.isdigit():
                idx_val = int(s_idx_str) - 1
                if 0 <= idx_val < len(all_streams_data):
                    indices_to_remove.append(idx_val)
                else:
                    invalid_inputs.append(s_idx_str)
            elif s_idx_str:
                invalid_inputs.append(s_idx_str)

        if invalid_inputs:
            console.print(
                f"Warning: Ignored invalid input(s): {', '.join(invalid_inputs)}",
                style="warning",
            )

        return sorted(list(set(indices_to_remove)), reverse=True)
    except ValueError:
        console.print("Invalid input format. Please enter numbers.", style="error")
        return []


def prompt_main_menu_action() -> str:
    """Gets user input for main menu actions."""
    try:
        choice = (
            input("Enter choice (or press Enter to select stream if live): ")
            .strip()
            .lower()
        )
        return choice
    except (EOFError, KeyboardInterrupt):
        return "q"


def show_playback_menu(
    stream_url: str, current_quality: str, has_next: bool, has_previous: bool
) -> Tuple[str, Optional[str]]:
    """
    Displays the interactive playback menu using prompt_toolkit.prompt in a loop.
    Returns an action string (e.g., "stop", "next", "quality", "donate", "quit")
    and potentially data (e.g., new quality string).
    """
    clear_screen()  # Keep current stream info visible if possible, or re-print
    console.print(
        f"Now Playing: [highlight]{stream_url}[/highlight] ([info]{current_quality}[/info])"
    )
    console.print("-" * 30, style="dimmed")

    text = Text()
    text.append("Playback Controls:\n", style="bold white")
    text.append("  [", style="dimmed").append("S", style="menu_key").append(
        "]top Stream\n", style="menu_option"
    )
    if has_next:
        text.append("  [", style="dimmed").append("N", style="menu_key").append(
            "]ext Stream\n", style="menu_option"
        )
    if has_previous:
        text.append("  [", style="dimmed").append("P", style="menu_key").append(
            "]revious Stream\n", style="menu_option"
        )
    text.append("  [", style="dimmed").append("C", style="menu_key").append(
        "]hange Quality\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("M", style="menu_key").append(
        "]ain Menu (stops current stream)\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("D", style="menu_key").append(
        "]onate to Developer\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("Q", style="menu_key").append(
        "]uit StreamWatch\n", style="menu_option"
    )
    console.print(text)
    console.print("-" * 30, style="dimmed")

    try:
        # Using prompt_toolkit.prompt for single character input with history disabled
        choice = (
            prompt(
                "Playback> ",
                style=playback_menu_style,
                # bottom_toolbar=lambda: " [S]top [N]ext [P]rev [C]hange [D]onate [Q]uit", # Example toolbar
                refresh_interval=0.5,  # To allow checking player status, see core.py
            )
            .strip()
            .lower()
        )
        return (choice, None)
    except (EOFError, KeyboardInterrupt):  # Ctrl+C or Ctrl+D
        return ("s", None)  # Treat as "stop stream" and return to main menu


def select_quality_dialog(
    available_qualities: List[str], current_quality: str
) -> Optional[str]:
    """
    Shows a dialog to select a new stream quality.
    Returns the selected quality string or None if cancelled or no change.
    """
    if not available_qualities:
        message_dialog(
            title="No Qualities",
            text="Could not retrieve available qualities for this stream.",
            style=dialog_style,
        ).run()
        return None

    choices = []
    default_selection = None
    for i, quality in enumerate(
        sorted(available_qualities, key=lambda q: (q != "best", q != "worst", q))
    ):  # Sort, with best/worst prioritized
        # The value to return is the quality string itself.
        display_text = f"[{i+1}] {quality}"
        if quality == current_quality:
            display_text += " (current)"
            default_selection = quality  # Set default for radiolist_dialog

        choices.append((quality, display_text))

    if not choices:  # Should not happen if available_qualities is not empty
        message_dialog(
            title="Error",
            text="No valid quality choices to display.",
            style=dialog_style,
        ).run()
        return None

    selected_quality = radiolist_dialog(
        title="Change Stream Quality",
        text="Select new quality:",
        values=choices,
        default=default_selection,  # Pre-select the current quality
        style=dialog_style,
    ).run()

    if selected_quality and selected_quality != current_quality:
        return str(selected_quality)
    elif selected_quality == current_quality:
        console.print("Selected quality is the same as current.", style="info")
        time.sleep(1)
    return None  # Cancelled or no change


__all__ = [
    "prompt_for_filepath",
    "select_stream_dialog",
    "prompt_add_streams",
    "prompt_remove_streams_dialog",
    "prompt_main_menu_action",
    "show_playback_menu",
    "select_quality_dialog",
]
