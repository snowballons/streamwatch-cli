import json
import sys
from . import config

def load_streams():
    """Loads the list of stream URLs from the JSON file."""
    if not config.STREAMS_FILE_PATH.exists():
        # Create an empty file if it doesn't exist
        save_streams([])
        return []
    try:
        with open(config.STREAMS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Basic validation: ensure all items are strings
                return [item for item in data if isinstance(item, str)]
            else:
                print(f"Warning: Invalid format in {config.STREAMS_FILE_PATH}. Expected a list.", file=sys.stderr)
                # Attempt recovery or return empty
                if isinstance(data.get("streams"), list): # Check for a common accidental structure
                     return [item for item in data["streams"] if isinstance(item, str)]
                return [] # Reset if format is wrong
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {config.STREAMS_FILE_PATH}.", file=sys.stderr)
        print("Creating a new empty stream list.", file=sys.stderr)
        save_streams([]) # Overwrite corrupted file
        return []
    except Exception as e:
        print(f"Error loading streams from {config.STREAMS_FILE_PATH}: {e}", file=sys.stderr)
        return []

def save_streams(streams):
    """Saves the list of stream URLs to the JSON file."""
    try:
        # Ensure parent directory exists (config.py should have created it, but double-check)
        config.STREAMS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.STREAMS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(streams, f, indent=4) # Use indent for readability
        return True
    except Exception as e:
        print(f"Error saving streams to {config.STREAMS_FILE_PATH}: {e}", file=sys.stderr)
        return False

def add_streams(new_urls):
    """Adds new URLs to the list, avoiding duplicates."""
    if not isinstance(new_urls, list):
        return False, "Invalid input type for new URLs."

    current_streams = load_streams()
    added_count = 0
    skipped_count = 0
    invalid_format_count = 0

    for url in new_urls:
        url = url.strip()
        if not url:
            continue

        # Basic URL format validation
        if not (url.startswith('http://') or url.startswith('https://')):
             print(f"Warning: Invalid format skipped: {url} (must start with http:// or https://)")
             invalid_format_count += 1
             continue

        if url not in current_streams:
            current_streams.append(url)
            added_count += 1
        else:
            skipped_count += 1

    if added_count > 0:
        if save_streams(current_streams):
             message = f"Successfully added {added_count} new stream(s)."
             if skipped_count > 0:
                 message += f" Skipped {skipped_count} duplicate(s)."
             if invalid_format_count > 0:
                 message += f" Skipped {invalid_format_count} due to invalid format."
             return True, message
        else:
             return False, "Failed to save updated stream list after adding."
    else:
        message = "No new streams were added."
        if skipped_count > 0:
            message += f" Skipped {skipped_count} duplicate(s)."
        if invalid_format_count > 0:
             message += f" Skipped {invalid_format_count} due to invalid format."
        return False, message # Indicate nothing was actually added/saved


def remove_streams_by_indices(indices_to_remove):
    """Removes streams from the list based on their 0-based indices."""
    current_streams = load_streams()
    if not indices_to_remove:
        return False, "No indices provided for removal."

    # Sort indices in descending order to avoid index shifting issues during removal
    indices_to_remove = sorted(list(set(indices_to_remove)), reverse=True)

    removed_count = 0
    skipped_invalid_count = 0
    actual_removed_urls = []

    for index in indices_to_remove:
        if 0 <= index < len(current_streams):
            removed_url = current_streams.pop(index)
            actual_removed_urls.append(removed_url)
            removed_count += 1
        else:
            skipped_invalid_count += 1

    if removed_count > 0:
        if save_streams(current_streams):
            message = f"Successfully removed {removed_count} stream(s)."
            if skipped_invalid_count > 0:
                message += f" Skipped {skipped_invalid_count} invalid index/indices."
            return True, message # Return the list of actually removed URLs? maybe just message
        else:
            return False, "Failed to save updated stream list after removal."
    else:
        message = "No streams were removed."
        if skipped_invalid_count > 0:
             message += f" Skipped {skipped_invalid_count} invalid index/indices."
        return False, message