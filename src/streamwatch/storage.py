import json
import logging
from pathlib import Path  # Import Path for file operations
from typing import Any, Dict, List, Tuple

from . import config
from .stream_utils import parse_url_metadata

logger = logging.getLogger(config.APP_NAME + ".storage")


def load_streams() -> List[Dict[str, Any]]:
    """
    Loads stream data from streams.json AND from files in the streams.d directory.
    Handles migration from old format and merges sources, avoiding duplicates.

    Returns:
        List of stream dictionaries with 'url' and 'alias' keys
    """
    # --- Step 1: Load from the primary streams.json file ---
    json_streams_data = []
    if config.STREAMS_FILE_PATH.exists():
        try:
            with open(config.STREAMS_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Data Migration Logic (remains the same)
            if (
                data
                and isinstance(data, list)
                and len(data) > 0
                and isinstance(data[0], str)
            ):
                logger.warning(
                    "Old stream file format detected in streams.json. Migrating..."
                )
                migrated_streams = []
                for url in data:
                    parsed_info = parse_url_metadata(url)
                    alias = parsed_info.get("username", "Unnamed Stream")
                    migrated_streams.append({"url": url, "alias": alias})

                if save_streams(migrated_streams):
                    logger.info("Successfully migrated streams.json.")
                    json_streams_data = migrated_streams
                else:
                    logger.error("Failed to save migrated streams.json.")
                    json_streams_data = (
                        migrated_streams  # Use in-memory for this session
                    )
            elif isinstance(data, list):
                # Assume new format
                json_streams_data = [
                    item for item in data if isinstance(item, dict) and "url" in item
                ]
            else:
                logger.warning(
                    "streams.json is not a list. It will be ignored for this session."
                )

        except (json.JSONDecodeError, FileNotFoundError):
            logger.error(
                "Could not read or decode streams.json. It will be ignored.",
                exc_info=True,
            )

    # --- Step 2: Load from the streams.d directory ---
    streams_d_path = config.USER_CONFIG_DIR / "streams.d"
    dir_streams_data = []
    if streams_d_path.is_dir():
        logger.debug(f"Found streams.d directory at {streams_d_path}. Loading streams.")
        for filepath in streams_d_path.iterdir():
            if filepath.is_file():  # Ignore subdirectories
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            url = line.strip()
                            if url and not url.startswith(
                                "#"
                            ):  # Ignore comments and empty lines
                                # Create a dict structure consistent with streams.json
                                # Auto-generate alias from the URL.
                                parsed_info = parse_url_metadata(url)
                                alias = parsed_info.get("username", "Unnamed Stream")
                                dir_streams_data.append({"url": url, "alias": alias})
                except Exception:
                    logger.error(
                        f"Failed to read or parse file in streams.d: {filepath}",
                        exc_info=True,
                    )

    # --- Step 3: Merge sources and remove duplicates ---
    # We prioritize streams from streams.json. If a URL is in both, the alias from streams.json is kept.
    final_streams_data = []
    seen_urls = set()

    # First, add all streams from streams.json
    for stream_data in json_streams_data:
        url = stream_data.get("url")
        if url and url not in seen_urls:
            final_streams_data.append(stream_data)
            seen_urls.add(url)

    # Then, add streams from streams.d/ directory, checking for duplicates
    for stream_data in dir_streams_data:
        url = stream_data.get("url")
        if url and url not in seen_urls:
            final_streams_data.append(stream_data)
            seen_urls.add(url)

    logger.info(
        f"Loaded {len(json_streams_data)} streams from json, {len(dir_streams_data)} from streams.d. Total unique: {len(final_streams_data)}."
    )
    return final_streams_data


def save_streams(streams_data: List[Dict[str, Any]]) -> bool:
    """Saves the list of stream data objects to the JSON file.

    Args:
        streams_data: List of stream dictionaries to save

    Returns:
        True if successful, False otherwise
    """
    try:
        config.USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.STREAMS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(streams_data, f, indent=4)
        return True
    except Exception:
        logger.error(
            "Error saving streams to %s", config.STREAMS_FILE_PATH, exc_info=True
        )
        return False


def add_streams(new_streams_data: List[Dict[str, str]]) -> Tuple[bool, str]:
    """
    Adds new stream data objects to the list, avoiding duplicate URLs.

    Args:
        new_streams_data: List of dicts with 'url' and 'alias' keys

    Returns:
        Tuple of (success_bool, message_str)
    """
    current_streams_data = load_streams()
    current_urls = {s["url"] for s in current_streams_data}

    added_count = 0
    skipped_count = 0
    invalid_format_count = 0

    for new_stream in new_streams_data:
        url = new_stream.get("url", "").strip()
        alias = new_stream.get("alias", "").strip()

        if not url:
            continue

        if not (url.startswith("http://") or url.startswith("https://")):
            logger.warning(f"Invalid URL format skipped: {url}")
            invalid_format_count += 1
            continue

        if url not in current_urls:
            if not alias:
                parsed_info = parse_url_metadata(url)
                alias = parsed_info.get("username", "Unnamed Stream")
            current_streams_data.append({"url": url, "alias": alias})
            current_urls.add(url)
            added_count += 1
        else:
            skipped_count += 1

    if added_count > 0:
        if save_streams(current_streams_data):
            message = f"Successfully added {added_count} new stream(s)."
            if skipped_count > 0:
                message += f" Skipped {skipped_count} duplicate(s)."
            if invalid_format_count > 0:
                message += f" Skipped {invalid_format_count} due to invalid format."
            return True, message
        else:
            return False, "Failed to save updated stream list."
    else:
        message = "No new streams were added."
        if skipped_count > 0:
            message += f" Skipped {skipped_count} duplicate(s)."
        if invalid_format_count > 0:
            message += f" Skipped {invalid_format_count} due to invalid format."
        return False, message


def remove_streams_by_indices(indices_to_remove: List[int]) -> Tuple[bool, str]:
    """Removes streams from the list based on their 0-based indices.

    Args:
        indices_to_remove: List of 0-based indices to remove

    Returns:
        Tuple of (success_bool, message_str)
    """
    current_streams = load_streams()
    if not indices_to_remove:
        return False, "No indices provided for removal."

    indices_to_remove = sorted(list(set(indices_to_remove)), reverse=True)
    removed_count = 0
    skipped_invalid_count = 0

    for index in indices_to_remove:
        if 0 <= index < len(current_streams):
            current_streams.pop(index)
            removed_count += 1
        else:
            skipped_invalid_count += 1

    if removed_count > 0:
        if save_streams(current_streams):
            message = f"Successfully removed {removed_count} stream(s)."
            if skipped_invalid_count > 0:
                message += f" Skipped {skipped_invalid_count} invalid index/indices."
            return True, message
        else:
            return False, "Failed to save updated stream list after removal."
    else:
        message = "No streams were removed."
        if skipped_invalid_count > 0:
            message += f" Skipped {skipped_invalid_count} invalid index/indices."
        return False, message


# --- NEW IMPORT/EXPORT FUNCTIONS ---


def import_streams_from_txt(filepath: Path) -> Tuple[bool, str]:
    """
    Reads a .txt file with one URL per line and adds them to the stream list.

    Args:
        filepath: Path to the text file to import

    Returns:
        Tuple of (success_bool, message_str)
    """
    try:
        source_path = Path(filepath).expanduser()  # Expand ~ for home directory
        if not source_path.is_file():
            return False, f"Import file not found at: {source_path}"

        with open(source_path, "r", encoding="utf-8") as f:
            urls_to_import = [line.strip() for line in f if line.strip()]

        if not urls_to_import:
            return False, "Import file is empty or contains no valid lines."

        # We will add these with auto-generated aliases.
        # The add_streams function expects a list of dicts.
        new_streams_data = [{"url": url, "alias": ""} for url in urls_to_import]

        # Use the existing add_streams logic to handle duplicates and saving
        success, message = add_streams(new_streams_data)

        # Refine the message for import context
        if success:
            import_message = f"Import successful. {message}"
            return True, import_message
        else:
            # add_streams returns a message even on "failure" (e.g., all duplicates)
            import_message = f"Import finished. {message}"
            return False, import_message

    except Exception as e:
        logger.error("Failed to import from file %s", filepath, exc_info=True)
        return False, f"An error occurred during import: {e}"


def export_streams_to_json(filepath: Path) -> Tuple[bool, str]:
    """
    Exports the current stream list (with aliases) to a JSON file.

    Args:
        filepath: Path where to export the JSON file

    Returns:
        Tuple of (success_bool, message_str)
    """
    try:
        destination_path = Path(filepath).expanduser()
        # Ensure parent directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        current_streams_data = load_streams()

        if not current_streams_data:
            return False, "There are no streams to export."

        with open(destination_path, "w", encoding="utf-8") as f:
            json.dump(current_streams_data, f, indent=4)

        logger.info(
            f"Successfully exported {len(current_streams_data)} streams to {destination_path}"
        )
        return (
            True,
            f"Successfully exported {len(current_streams_data)} streams to {destination_path}",
        )

    except Exception as e:
        logger.error("Failed to export to file %s", filepath, exc_info=True)
        return False, f"An error occurred during export: {e}"
