"""
StreamWatch UI Display Module

This module contains all display and presentation functions for the StreamWatch CLI application.
It handles rendering of menus, stream lists, messages, and other visual elements.
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Union

from prompt_toolkit import prompt
from rich.text import Text

from .. import config
from .styles import STREAM_DISPLAY_COLORS, console, dialog_style

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".ui.display")


def clear_screen() -> None:
    """Clears the terminal screen."""
    try:
        if os.name == "nt":
            subprocess.run(["cls"], shell=True, check=False)  # nosec B602
        else:
            subprocess.run(["clear"], check=False)  # nosec B603
    except Exception:
        pass  # Ignore errors if clear command fails
    logger.debug("Screen cleared.")


def display_main_menu(live_streams_count: int) -> None:
    """Displays the main menu options."""
    logger.info(f"Displaying main menu. Live streams count: {live_streams_count}")
    console.print("------------------------------------", style="dimmed")
    console.print("Main Menu Options:", style="bold white")
    text = Text()
    if live_streams_count > 0:
        text.append("  [", style="dimmed").append("Enter", style="menu_key").append(
            "]  - Select & Play live stream\n", style="menu_option"
        )
    text.append("  [", style="dimmed").append("L", style="menu_key").append(
        "]      - List all configured streams\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("A", style="menu_key").append(
        "]      - Add new stream URL(s)\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("R", style="menu_key").append(
        "]      - Remove configured stream(s)\n", style="menu_option"
    )

    # --- NEW MENU OPTIONS ---
    text.append("  [", style="dimmed").append("I", style="menu_key").append(
        "]      - Import streams from .txt file\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("E", style="menu_key").append(
        "]      - Export streams to .json file\n", style="menu_option"
    )
    # --- END NEW ---

    text.append("  [", style="dimmed").append("P", style="menu_key").append(
        "]lay Last Stream\n", style="menu_option"
    ) if config.get_last_played_url() else None
    text.append("  [", style="dimmed").append("F", style="menu_key").append(
        "]      - Refresh live stream list\n", style="menu_option"
    )
    text.append("  [", style="dimmed").append("Q", style="menu_key").append(
        "]      - Quit\n", style="menu_option"
    )
    console.print(text)
    console.print("------------------------------------", style="dimmed")


def format_viewer_count(count: Optional[int]) -> str:
    """Formats the viewer count nicely (e.g., 1234 -> 1.2K)."""
    if count is None or not isinstance(count, (int, float)):
        return ""  # Return empty string if no count is available

    if count < 1000:
        return f"{count}"
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"


def format_stream_for_display(
    stream_info: Dict[str, Any],
    index: Optional[int] = None,
    for_prompt_toolkit: bool = False,
) -> Union[Text, str]:
    """Now includes viewer count in the display."""
    text = Text()
    colors = STREAM_DISPLAY_COLORS

    if isinstance(stream_info, dict):
        if index is not None:
            text.append(f"[{index + 1}] ", style=colors["num_color"])

        display_name = stream_info.get("alias") or stream_info.get("username", "N/A")
        text.append(str(display_name), style=colors["username_color"])
        text.append(
            f" ({stream_info.get('platform', 'N/A')})", style=colors["platform_color"]
        )

        # --- NEW: Viewer Count Display ---
        viewer_count = stream_info.get("viewer_count")
        if viewer_count is not None:
            formatted_count = format_viewer_count(viewer_count)
            # Using an icon like a person emoji or a dot adds a nice touch
            text.append(f" │ 👁️ {formatted_count}", style=colors["viewer_color"])
        # --- END NEW ---

        text.append(
            f" - {stream_info.get('category_keywords', 'N/A')}",
            style=colors["category_color"],
        )
    elif isinstance(stream_info, str):
        if index is not None:
            text.append(f"[{index + 1}] ", style=colors["num_color"])
        text.append(stream_info, style="dim white")
    elif (
        isinstance(stream_info, tuple) and len(stream_info) == 2
    ):  # New: Handle (index, data) for removal
        idx, data = stream_info
        text.append(f"[{idx + 1}] ", style=colors["num_color"])
        text.append(
            str(data.get("alias", data.get("url"))), style=colors["username_color"]
        )  # Show alias
        text.append(f" ({data.get('url')})", style="dimmed")  # Show URL dimmed
    else:
        text.append("Invalid stream data", style="error")

    if for_prompt_toolkit:
        return str(text)
    return text


def display_stream_list(
    stream_info_list: List[Dict[str, Any]], title: str = "--- Available Streams ---"
) -> None:
    """Displays a list of streams with their metadata (less interactive, more for general display)."""
    clear_screen()
    console.print(Text(title, style="title"))
    if not stream_info_list:
        console.print("  (No streams to display)", style="dimmed")
        console.print()
        return

    for i, stream_info in enumerate(stream_info_list):
        formatted_text = format_stream_for_display(stream_info, i)
        console.print(f"  {formatted_text}")
    console.print()


def display_urls_for_removal(
    all_streams: List[Dict[str, Any]],
    title: str = "--- Configured Streams (for removal) ---",
) -> None:
    console.print(title, style="title")
    if not all_streams:
        console.print(" (No streams to display)", style="dimmed")
        return
    for i, url in enumerate(all_streams):
        console.print(f"  {format_stream_for_display(url, i)}")


def show_message(
    message: str, style: str = "info", duration: float = 1.5, pause_after: bool = False
) -> None:
    """Displays a message for a short duration."""
    logger.info(f"Show message: {message} (style={style})")
    console.print(f"\n{message}", style=style)
    if duration > 0:
        time.sleep(duration)
    if pause_after:
        try:
            prompt("\nPress Enter to continue...", style=dialog_style)
        except (EOFError, KeyboardInterrupt):
            pass


__all__ = [
    "clear_screen",
    "display_main_menu",
    "display_stream_list",
    "format_stream_for_display",
    "format_viewer_count",
    "display_urls_for_removal",
    "show_message",
]
