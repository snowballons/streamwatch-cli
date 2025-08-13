"""
StreamWatch UI Styles Module

This module contains all styling constants, themes, and style definitions
used throughout the StreamWatch CLI application.
"""

from prompt_toolkit.styles import Style
from rich.console import Console
from rich.theme import Theme

# Rich theme for console styling
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "green",
        "highlight": "bold magenta",
        "dimmed": "dim",
        "title": "bold white on blue",
        "menu_option": "cyan",
        "menu_key": "bold yellow",
    }
)

# Console instance with custom theme
console = Console(theme=custom_theme)

# Prompt toolkit style for dialogs
dialog_style = Style.from_dict(
    {
        "dialog": "bg:#333333 #dddddd",
        "dialog frame.label": "bg:#555555 #ffffff",
        "dialog.body": "bg:#222222 #cccccc",
        "button": "bg:#000000 #ffffff",
        "radio": "",
        "radio-selected": "#33dd33",
        "checkbox": "",
        "checkbox-selected": "#33dd33",
    }
)

# Prompt toolkit style for playback menu
playback_menu_style = Style.from_dict(
    {
        "prompt-prefix": "bg:#111111 #ansicyan",
        "selected-text": "bg:#555555 #ffffff",
    }
)

# Color constants for stream display formatting
STREAM_DISPLAY_COLORS = {
    "num_color": "bold white",
    "username_color": "bold cyan",
    "platform_color": "blue",
    "category_color": "default",
    "viewer_color": "bold red",
}

__all__ = [
    "custom_theme",
    "console",
    "dialog_style",
    "playback_menu_style",
    "STREAM_DISPLAY_COLORS",
]
