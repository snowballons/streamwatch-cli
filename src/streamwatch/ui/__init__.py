"""
StreamWatch UI Module

This module provides the user interface components for the StreamWatch CLI application.
It separates concerns between display logic, input handling, and styling.
"""

# Import display functions
from .display import (
    clear_screen,
    display_main_menu,
    display_stream_list,
    display_urls_for_removal,
    format_stream_for_display,
    format_viewer_count,
    show_message,
)

# Import input handling functions
from .input_handler import (
    prompt_add_streams,
    prompt_for_filepath,
    prompt_main_menu_action,
    prompt_remove_streams_dialog,
    select_quality_dialog,
    select_stream_dialog,
    show_playback_menu,
)

# Import styles and console for backward compatibility
from .styles import (
    STREAM_DISPLAY_COLORS,
    console,
    custom_theme,
    dialog_style,
    playback_menu_style,
)

__all__ = [
    # Display functions
    "clear_screen",
    "display_main_menu",
    "display_stream_list",
    "format_stream_for_display",
    "format_viewer_count",
    "display_urls_for_removal",
    "show_message",
    # Input functions
    "prompt_main_menu_action",
    "prompt_add_streams",
    "select_stream_dialog",
    "show_playback_menu",
    "select_quality_dialog",
    "prompt_remove_streams_dialog",
    "prompt_for_filepath",
    # Console and styles (for backward compatibility)
    "console",
    "custom_theme",
    "dialog_style",
    "playback_menu_style",
    "STREAM_DISPLAY_COLORS",
]