import os
import time
import logging # Import logging
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog, message_dialog, button_dialog
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.text import Text
from rich.theme import Theme

from . import config

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".ui")

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "green",
    "highlight": "bold magenta",
    "dimmed": "dim",
    "title": "bold white on blue",
    "menu_option": "cyan",
    "menu_key": "bold yellow"
})
console = Console(theme=custom_theme)

dialog_style = Style.from_dict({
    'dialog':             'bg:#333333 #dddddd',
    'dialog frame.label': 'bg:#555555 #ffffff',
    'dialog.body':        'bg:#222222 #cccccc',
    'button':             'bg:#000000 #ffffff',
    'radio':              '',
    'radio-selected':     '#33dd33',
    'checkbox':           '',
    'checkbox-selected':  '#33dd33',
})

playback_menu_style = Style.from_dict({
    'prompt-prefix': 'bg:#111111 #ansicyan',
    'selected-text': 'bg:#555555 #ffffff',
})

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
    logger.debug("Screen cleared.")

def display_main_menu(live_streams_count):
    """Displays the main menu options."""
    logger.info(f"Displaying main menu. Live streams count: {live_streams_count}")
    console.print("------------------------------------", style="dimmed")
    console.print("Main Menu Options:", style="bold white")
    text = Text()
    if live_streams_count > 0:
        text.append("  [", style="dimmed").append("Enter", style="menu_key").append("]  - Select & Play live stream\n", style="menu_option")
    text.append("  [", style="dimmed").append("L", style="menu_key").append("]      - List all configured streams\n", style="menu_option")
    text.append("  [", style="dimmed").append("A", style="menu_key").append("]      - Add new stream URL(s)\n", style="menu_option")
    text.append("  [", style="dimmed").append("R", style="menu_key").append("]      - Remove configured stream(s)\n", style="menu_option")
    text.append("  [", style="dimmed").append("F", style="menu_key").append("]      - Refresh live stream list\n", style="menu_option")
    if config.get_last_played_url(): # Only show if there's a last played URL
        text.append("  [", style="dimmed").append("P", style="menu_key").append("]lay Last Stream\n", style="menu_option")
    text.append("  [", style="dimmed").append("Q", style="menu_key").append("]uit StreamWatch\n", style="menu_option")
    console.print(text)
    console.print("------------------------------------", style="dimmed")

def format_stream_for_display(stream_info, index=None, for_prompt_toolkit=False):
    text = Text()
    num_color = "bold white"
    username_color = "bold cyan"
    platform_color = "blue"
    category_color = "default"

    if isinstance(stream_info, dict):
        if index is not None:
            text.append(f"[{index + 1}] ", style=num_color)
        text.append(str(stream_info.get('username', 'N/A')), style=username_color)
        text.append(f" ({stream_info.get('platform', 'N/A')})", style=platform_color)
        text.append(f" - {stream_info.get('category_keywords', 'N/A')}", style=category_color)
    elif isinstance(stream_info, str):
        if index is not None:
            text.append(f"[{index + 1}] ", style=num_color)
        text.append(stream_info, style="dim white")
    else:
        text.append("Invalid stream data", style="error")

    if for_prompt_toolkit:
        return str(text)
    return text

def display_stream_list(stream_info_list, title="--- Available Streams ---"):
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

def select_stream_dialog(stream_info_list, title="Select a stream to play", prompt_text="Choose a stream:"):
    """Displays an interactive dialog to select a stream."""
    if not stream_info_list:
        message_dialog(title="No Streams", text="There are no streams available to select.", style=dialog_style).run()
        return None

    choices = []
    for i, s_info in enumerate(stream_info_list):
        display_text_str = format_stream_for_display(s_info, index=i, for_prompt_toolkit=True)
        choices.append( (s_info, display_text_str) )

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
        title=title,
        text=str(rich_prompt_text),
        values=choices,
        style=dialog_style
    ).run()
    return selected_stream_info

def prompt_add_streams():
    """Prompts the user to enter stream URLs to add using prompt_toolkit."""
    clear_screen()
    console.print("--- Add New Stream(s) ---", style="title")
    console.print("Enter stream URL(s). You can add multiple URLs separated by commas (,).")
    console.print("Press Ctrl+D or Ctrl+C (or Esc then Enter on Windows) to cancel.", style="dimmed")
    try:
        urls_input = prompt("URL(s): ", style=dialog_style)
        if not urls_input:
            return []
        return [url.strip() for url in urls_input.split(',') if url.strip()]
    except (EOFError, KeyboardInterrupt):
        console.print("\nAdd operation cancelled.", style="warning")
        return []

def display_urls_for_removal(all_streams, title="--- Configured Streams (for removal) ---"):
    console.print(title, style="title")
    if not all_streams:
        console.print(" (No streams to display)", style="dimmed")
        return
    for i, url in enumerate(all_streams):
        console.print(f"  {format_stream_for_display(url, i)}")

def prompt_remove_streams_dialog(all_stream_urls, title="Select streams to REMOVE"):
    """Displays a dialog to select multiple streams for removal."""
    if not all_stream_urls:
        message_dialog(title="No Streams", text="There are no configured streams to remove.", style=dialog_style).run()
        return None

    clear_screen()
    display_urls_for_removal(all_stream_urls, title=title)
    
    console.print("\nEnter the number(s) of the stream(s) you want to remove.")
    console.print("Multiple numbers separated by spaces or commas (e.g., 1 3 4 or 1,3,4).", style="dimmed")
    console.print("Press Ctrl+D or Ctrl+C (or Esc then Enter on Windows) to cancel.", style="dimmed")

    try:
        choice_input = prompt("Remove number(s): ", style=dialog_style)
        if not choice_input: return []
    except (EOFError, KeyboardInterrupt):
        console.print("\nRemove operation cancelled.", style="warning")
        return []

    try:
        raw_indices_str = choice_input.replace(',', ' ').split()
        indices_to_remove = []
        invalid_inputs = []
        for s_idx_str in raw_indices_str:
            s_idx_str = s_idx_str.strip()
            if s_idx_str.isdigit():
                idx_val = int(s_idx_str) - 1
                if 0 <= idx_val < len(all_stream_urls):
                    indices_to_remove.append(idx_val)
                else:
                    invalid_inputs.append(s_idx_str)
            elif s_idx_str:
                invalid_inputs.append(s_idx_str)
        
        if invalid_inputs:
            console.print(f"Warning: Ignored invalid input(s): {', '.join(invalid_inputs)}", style="warning")

        return sorted(list(set(indices_to_remove)), reverse=True)
    except ValueError:
        console.print("Invalid input format. Please enter numbers.", style="error")
        return []

def prompt_main_menu_action():
    """Gets user input for main menu actions."""
    try:
        choice = input("Enter choice (or press Enter to select stream if live): ").strip().lower()
        return choice
    except (EOFError, KeyboardInterrupt):
        return "q"

def show_message(message, style="info", duration=1.5, pause_after=False):
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

def show_playback_menu(stream_url, current_quality, has_next, has_previous):
    """
    Displays the interactive playback menu using prompt_toolkit.prompt in a loop.
    Returns an action string (e.g., "stop", "next", "quality", "donate", "quit")
    and potentially data (e.g., new quality string).
    """
    clear_screen() # Keep current stream info visible if possible, or re-print
    console.print(f"Now Playing: [highlight]{stream_url}[/highlight] ([info]{current_quality}[/info])")
    console.print("-" * 30, style="dimmed")
    
    text = Text()
    text.append("Playback Controls:\n", style="bold white")
    text.append("  [", style="dimmed").append("S", style="menu_key").append("]top Stream\n", style="menu_option")
    if has_next:
        text.append("  [", style="dimmed").append("N", style="menu_key").append("]ext Stream\n", style="menu_option")
    if has_previous:
        text.append("  [", style="dimmed").append("P", style="menu_key").append("]revious Stream\n", style="menu_option")
    text.append("  [", style="dimmed").append("C", style="menu_key").append("]hange Quality\n", style="menu_option")
    text.append("  [", style="dimmed").append("M", style="menu_key").append("]ain Menu (stops current stream)\n", style="menu_option")
    text.append("  [", style="dimmed").append("D", style="menu_key").append("]onate to Developer\n", style="menu_option")
    text.append("  [", style="dimmed").append("Q", style="menu_key").append("]uit StreamWatch\n", style="menu_option")
    console.print(text)
    console.print("-" * 30, style="dimmed")

    try:
        # Using prompt_toolkit.prompt for single character input with history disabled
        choice = prompt(
            "Playback> ",
            style=playback_menu_style,
            # bottom_toolbar=lambda: " [S]top [N]ext [P]rev [C]hange [D]onate [Q]uit", # Example toolbar
            refresh_interval=0.5 # To allow checking player status, see core.py
        ).strip().lower()
        return choice
    except (EOFError, KeyboardInterrupt): # Ctrl+C or Ctrl+D
        return "s" # Treat as "stop stream" and return to main menu


def select_quality_dialog(available_qualities, current_quality):
    """
    Shows a dialog to select a new stream quality.
    Returns the selected quality string or None if cancelled or no change.
    """
    if not available_qualities:
        message_dialog(title="No Qualities", text="Could not retrieve available qualities for this stream.", style=dialog_style).run()
        return None

    choices = []
    default_selection = None
    for i, quality in enumerate(sorted(available_qualities, key=lambda q: (q != 'best', q != 'worst', q))): # Sort, with best/worst prioritized
        # The value to return is the quality string itself.
        display_text = f"[{i+1}] {quality}"
        if quality == current_quality:
            display_text += " (current)"
            default_selection = quality # Set default for radiolist_dialog

        choices.append((quality, display_text))
    
    if not choices: # Should not happen if available_qualities is not empty
        message_dialog(title="Error", text="No valid quality choices to display.", style=dialog_style).run()
        return None

    selected_quality = radiolist_dialog(
        title="Change Stream Quality",
        text="Select new quality:",
        values=choices,
        default=default_selection, # Pre-select the current quality
        style=dialog_style
    ).run()

    if selected_quality and selected_quality != current_quality:
        return selected_quality
    elif selected_quality == current_quality:
        console.print("Selected quality is the same as current.", style="info")
        time.sleep(1)
    return None # Cancelled or no change