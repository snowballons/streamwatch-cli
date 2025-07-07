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

def prompt_for_filepath(prompt_text="Enter file path: ", default_filename=""):
    """Prompts the user to enter a file path."""
    console.print(f"Enter the path for the file. You can use `~` for your home directory.")
    console.print("Press Ctrl+D or Ctrl+C to cancel.", style="dimmed")
    try:
        # prompt_toolkit's prompt has a `default` argument
        filepath = prompt(prompt_text, default=default_filename, style=dialog_style)
        return filepath.strip() if filepath else None
    except (EOFError, KeyboardInterrupt):
        console.print("\nOperation cancelled.", style="warning")
        return None


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

    # --- NEW MENU OPTIONS ---
    text.append("  [", style="dimmed").append("I", style="menu_key").append("]      - Import streams from .txt file\n", style="menu_option")
    text.append("  [", style="dimmed").append("E", style="menu_key").append("]      - Export streams to .json file\n", style="menu_option")
    # --- END NEW ---

    text.append("  [", style="dimmed").append("P", style="menu_key").append("]lay Last Stream\n", style="menu_option") if config.get_last_played_url() else None
    text.append("  [", style="dimmed").append("F", style="menu_key").append("]      - Refresh live stream list\n", style="menu_option")
    text.append("  [", style="dimmed").append("Q", style="menu_key").append("]      - Quit\n", style="menu_option")
    console.print(text)
    console.print("------------------------------------", style="dimmed")

def format_viewer_count(count):
    """Formats the viewer count nicely (e.g., 1234 -> 1.2K)."""
    if count is None or not isinstance(count, (int, float)):
        return "" # Return empty string if no count is available

    if count < 1000:
        return f"{count}"
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"


def format_stream_for_display(stream_info, index=None, for_prompt_toolkit=False):
    """Now includes viewer count in the display."""
    text = Text()
    num_color = "bold white"
    username_color = "bold cyan"
    platform_color = "blue"
    category_color = "default"
    viewer_color = "bold red" # Make viewer count stand out

    if isinstance(stream_info, dict):
        if index is not None:
            text.append(f"[{index + 1}] ", style=num_color)

        display_name = stream_info.get('alias') or stream_info.get('username', 'N/A')
        text.append(str(display_name), style=username_color)
        text.append(f" ({stream_info.get('platform', 'N/A')})", style=platform_color)

        # --- NEW: Viewer Count Display ---
        viewer_count = stream_info.get('viewer_count')
        if viewer_count is not None:
            formatted_count = format_viewer_count(viewer_count)
            # Using an icon like a person emoji or a dot adds a nice touch
            text.append(f" │ 👁️ {formatted_count}", style=viewer_color)
        # --- END NEW ---

        text.append(f" - {stream_info.get('category_keywords', 'N/A')}", style=category_color)
    elif isinstance(stream_info, str):
        if index is not None:
            text.append(f"[{index + 1}] ", style=num_color)
        text.append(stream_info, style="dim white")
    elif isinstance(stream_info, tuple) and len(stream_info) == 2: # New: Handle (index, data) for removal
        idx, data = stream_info
        text.append(f"[{idx + 1}] ", style=num_color)
        text.append(str(data.get('alias', data.get('url'))), style=username_color) # Show alias
        text.append(f" ({data.get('url')})", style="dimmed") # Show URL dimmed
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
    """Prompts the user for URLs and optional aliases."""
    clear_screen()
    console.print("--- Add New Stream(s) ---", style="title")
    console.print("Enter stream URL(s). You can provide an optional alias after the URL with a space.")
    console.print("Example: [cyan]https://twitch.tv/shroud My Favorite FPS[/cyan]")
    console.print("Example (multiple): [cyan]https://youtube.com/@LTT, https://twitch.tv/pokimane Queen Poki[/cyan]")
    console.print("Press Ctrl+D or Ctrl+C to cancel.", style="dimmed")

    try:
        urls_input = prompt("URL(s) [and optional alias(es)]: ", style=dialog_style)
        if not urls_input:
            return []

        new_streams_data = []
        # Split by comma first to handle multiple entries
        entries = urls_input.split(',')
        for entry in entries:
            entry = entry.strip()
            if not entry: continue

            parts = entry.split(maxsplit=1) # Split only on the first space
            url = parts[0]
            alias = parts[1] if len(parts) > 1 else ""
            new_streams_data.append({'url': url.strip(), 'alias': alias.strip()})

        return new_streams_data
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

def prompt_remove_streams_dialog(all_streams_data, title="Select streams to REMOVE"):
    """Now displays alias and URL for easier identification."""
    if not all_streams_data:
        message_dialog(title="No Streams", text="There are no configured streams to remove.", style=dialog_style).run()
        return None

    clear_screen()
    console.print("--- Remove Configured Stream(s) ---", style="title")
    for i, s_data in enumerate(all_streams_data):
        console.print(f"  [{i+1}] [highlight]{s_data.get('alias', s_data.get('url'))}[/highlight] [dim]({s_data.get('url')})[/dim]")

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
                if 0 <= idx_val < len(all_streams_data):
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
