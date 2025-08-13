import json  # For parsing --json output
import logging  # Import logging
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from . import config
from .models import StreamInfo, StreamMetadata, StreamStatus
from .stream_utils import parse_url_metadata  # IMPORT THE NEW FUNCTION

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".stream_checker")


def is_stream_live_for_check(url: str) -> Tuple[bool, str]:
    """
    Checks if a given stream URL is currently live using streamlink.

    Args:
        url: The stream URL to check

    Returns:
        Tuple of (is_live, url)
    """
    command = ["streamlink"]
    if config.get_twitch_disable_ads():
        command.append("--twitch-disable-ads")
    command.append(url)

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=config.get_streamlink_timeout_liveness(),
            check=False,
        )
        if process.returncode == 0 and "Available streams:" in process.stdout:
            logger.debug(f"Stream is live: {url}")
            return True, url

        stderr_lower = process.stderr.lower()
        stdout_lower = process.stdout.lower()
        if (
            "no playable streams found" in stderr_lower
            or "error: no streams found on" in stderr_lower
            or "this stream is offline" in stdout_lower
            or process.returncode != 0
        ):
            logger.info(f"Stream is not live: {url}")
            return False, url
        logger.warning(f"Ambiguous liveness result for: {url}")
        return False, url  # Default to not live for ambiguous cases
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout expired checking liveness for: {url}")
        return False, url
    except FileNotFoundError:
        logger.critical("streamlink command not found during check.")
        raise FileNotFoundError("streamlink command not found during check.")
    except (
        Exception
    ) as e:  # Catch any other exception during the check for a single stream
        logger.exception(f"Error checking liveness for {url}")
        return False, url


def get_stream_metadata_json(url: str) -> Tuple[bool, str]:
    """Fetches stream metadata using streamlink --json.

    Args:
        url: The stream URL to get metadata for

    Returns:
        Tuple of (success, json_string_or_error_message)
    """
    command = ["streamlink", "--twitch-disable-ads", url, "--json"]
    if (
        config.get_twitch_disable_ads() and "twitch.tv" in url
    ):  # Ensure flag is relevant
        pass  # Already included --twitch-disable-ads
    elif "--twitch-disable-ads" in command and "twitch.tv" not in url:
        command.remove("--twitch-disable-ads")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=config.get_streamlink_timeout_metadata(),  # Slightly longer timeout for JSON
            check=False,  # Don't crash on non-zero, parse stderr
        )
        if process.returncode == 0 and process.stdout:
            try:
                return (True, process.stdout)
            except Exception as e:
                logger.warning(f"Could not process JSON for {url}: {e}")
                return (False, f"JSON processing error: {e}")
        logger.warning(
            f"streamlink --json for {url} failed. stderr: {process.stderr[:100]}"
        )
        return (
            False,
            f"streamlink failed: {process.stderr[:100] if process.stderr else 'Unknown error'}",
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout fetching JSON metadata for {url}")
        return (False, "Timeout expired")
    except FileNotFoundError:
        logger.critical("streamlink command not found during JSON metadata fetch.")
        raise FileNotFoundError(
            "streamlink command not found during JSON metadata fetch."
        )
    except Exception as e:
        logger.exception(f"Error fetching JSON metadata for {url}")
        return None


def extract_category_keywords(
    metadata_result: Tuple[bool, str], platform: str, url_type: str = "unknown"
) -> str:
    """Extracts category/keywords from streamlink's JSON metadata based on platform.

    Args:
        metadata_result: Tuple of (success, json_string_or_error) from get_stream_metadata_json
        platform: The platform name (e.g., 'Twitch', 'YouTube')
        url_type: The type of URL being processed

    Returns:
        Category string or 'N/A' if not found
    """
    success, json_data = metadata_result
    if not success:
        return "N/A"

    try:
        metadata_json = json.loads(json_data)
    except json.JSONDecodeError:
        return "N/A"

    if not metadata_json or "metadata" not in metadata_json:
        return "N/A"
    meta = metadata_json.get("metadata", {})
    title = meta.get("title", "")

    # Helper to clean titles
    def clean_common_prefixes(text: str) -> str:
        return re.sub(
            r"^\(?(LIVE|EN DIRECT|ОНЛАЙН|생방송|ライブ)[\]:]*\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

    # --- Platform Specific Logic ---
    if platform == "Twitch":
        return str(meta.get("game") or (title.split(" ")[0] if title else "N/A"))

    elif platform == "YouTube":
        clean_title = clean_common_prefixes(title)
        words = clean_title.split()
        if (
            len(words) > 0
            and len(words[0]) <= 2
            and len(words) > 1
            and words[0].upper()
            not in [
                "A",
                "AN",
                "BE",
                "IN",
                "IS",
                "IT",
                "OF",
                "ON",
                "OR",
                "SO",
                "TO",
                "EL",
                "LA",
                "DE",
            ]
        ):
            return " ".join(words[1:4]) if len(words) > 1 else clean_title
        return " ".join(words[:3]) if words else "N/A"

    elif platform == "Kick":
        # Kick often has category in title or a specific field if plugin supports
        # Assuming title is primary for now if no dedicated field found in your tests
        return (
            title.split(":")[0].strip()
            if ":" in title
            else (title.split(" ")[0] if title else "N/A")
        )

    elif platform == "TikTok" or platform == "Douyin" or platform == "Bigo Live":
        # Title is primary; may contain hints.
        return (
            clean_common_prefixes(title) if title else "N/A"
        )  # Return more of the title

    elif platform == "BiliBili":
        category = meta.get("game_name", meta.get("category"))
        if category:
            return str(category)
        return (
            clean_common_prefixes(title).split(" - ")[0]
            if " - " in title
            else (title.split(" ")[0] if title else "N/A")
        )

    elif platform == "Vimeo" or platform == "Dailymotion":
        # Title usually contains event/stream description
        return clean_common_prefixes(title) if title else "N/A"

    elif platform == "PlutoTV":
        return (
            meta.get("program_title") or meta.get("title") or "Live TV"
        )  # Current show

    elif platform == "Huya":
        return str(
            meta.get("game_name", meta.get("category"))
            or (title.split(" ")[0] if title else "N/A")
        )

    elif platform in [
        "BBC iPlayer",
        "RaiPlay",
        "Atresplayer",
        "RTVE Play",
        "ARD Mediathek",
        "ZDF Mediathek",
        "Mitele",
        "AbemaTV",
    ]:
        # For broadcasters, the program title is the category
        return meta.get("program_title", meta.get("title")) or "Live Broadcast"

    elif platform == "Adult Swim":
        return meta.get("title") or "Live Stream"  # Title is often the show

    elif platform == "Bloomberg":
        return meta.get("title") or "Live News"  # Title is the show/feed

    # --- Generic Fallback ---
    if title:
        clean_title = clean_common_prefixes(title)
        return " ".join(
            clean_title.split()[:3]
        )  # First 3 words of cleaned title as a generic category
    return "N/A"


def fetch_live_streams(
    all_configured_streams_data: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Fetches the list of currently live streams with enhanced metadata.

    Args:
        all_configured_streams_data: List of configured stream dictionaries

    Returns:
        List of dictionaries with stream info including live status and metadata
    """
    if not all_configured_streams_data:
        logger.info("No configured streams to check.")
        return []

    all_configured_urls = [s["url"] for s in all_configured_streams_data]
    url_to_alias_map = {
        s["url"]: s.get("alias", "") for s in all_configured_streams_data
    }

    logger.info("Checking stream liveness, please wait...")
    live_stream_candidates = []  # URLs that are live

    # Phase 1: Quick Liveness Check
    with ThreadPoolExecutor(max_workers=config.get_max_workers_liveness()) as executor:
        future_to_url = {
            executor.submit(is_stream_live_for_check, url): url
            for url in all_configured_urls
        }
        for future in as_completed(future_to_url):
            (
                is_live,
                url,
            ) = future.result()  # is_stream_live_for_check must return (bool, url)
            if is_live:
                live_stream_candidates.append(url)

    if not live_stream_candidates:
        logger.info("No streams appear to be live based on initial check.")
        return []

    logger.info(
        f"Found {len(live_stream_candidates)} potentially live stream(s). Fetching details..."
    )

    # Phase 2: Fetch detailed metadata for live candidates
    detailed_live_streams = []
    with ThreadPoolExecutor(max_workers=config.get_max_workers_metadata()) as executor:
        future_to_meta_task = {}
        for url in live_stream_candidates:
            parsed_initial_info = parse_url_metadata(url)
            future = executor.submit(get_stream_metadata_json, url)
            future_to_meta_task[future] = {
                "url": url,
                "initial_platform": parsed_initial_info["platform"],
                "initial_username": parsed_initial_info["username"],
                "url_type": parsed_initial_info.get("type", "unknown"),
            }

        for future in as_completed(future_to_meta_task):
            task_info = future_to_meta_task[future]
            url, initial_platform, initial_username, url_type = (
                task_info["url"],
                task_info["initial_platform"],
                task_info["initial_username"],
                task_info["url_type"],
            )

            final_username = initial_username
            final_platform = (
                initial_platform  # Usually doesn't change from initial parse
            )
            category = "N/A (no details)"

            try:
                metadata_result = future.result()
                success, json_data = metadata_result

                # --- NEW: Viewer Count Extraction ---
                viewer_count = None  # Default to None
                metadata_json = None
                meta = None

                if success:
                    try:
                        metadata_json = json.loads(json_data)
                        if metadata_json and "metadata" in metadata_json:
                            meta = metadata_json["metadata"]
                            # Check for common key names for viewer count
                            if "viewers" in meta:
                                viewer_count = meta["viewers"]
                            elif "viewer_count" in meta:
                                viewer_count = meta["viewer_count"]
                            # Add other platform-specific keys if discovered, e.g., meta.get('online')
                    except json.JSONDecodeError:
                        pass
                # --- END NEW ---

                if meta:
                    # Refine username based on platform-specific metadata fields
                    author_field = None
                    if final_platform == "Twitch":
                        author_field = meta.get("user_name")
                    elif final_platform == "YouTube":
                        author_field = meta.get(
                            "author", meta.get("channel", meta.get("uploader"))
                        )
                    elif final_platform == "Kick":
                        author_field = meta.get("user", {}).get("username")
                    elif final_platform in [
                        "TikTok",
                        "Douyin",
                        "BiliBili",
                        "Huya",
                        "Bigo Live",
                    ]:
                        author_field = meta.get("author", meta.get("nick"))
                    elif final_platform in ["Vimeo", "Dailymotion"]:
                        author_field = meta.get(
                            "uploader", meta.get("channel", meta.get("author"))
                        )
                    elif final_platform == "PlutoTV":
                        author_field = meta.get("channel_name", meta.get("station_id"))
                    elif final_platform == "BBC iPlayer":
                        author_field = meta.get(
                            "channel_title", meta.get("service_name")
                        )
                    elif final_platform == "RaiPlay":
                        author_field = meta.get("channel", meta.get("name"))
                    elif final_platform == "Atresplayer":
                        author_field = meta.get("channel_name")
                    elif final_platform == "RTVE Play":
                        author_field = meta.get("channel", meta.get("id"))
                    elif final_platform == "ARD Mediathek":
                        author_field = meta.get("channelTitle", meta.get("station"))
                    elif final_platform == "ZDF Mediathek":
                        author_field = meta.get("channel", meta.get("stationName"))
                    elif final_platform == "Mitele":
                        author_field = meta.get("channel_name")
                    elif final_platform == "AbemaTV":
                        author_field = meta.get("channelName")
                    elif final_platform == "Adult Swim":
                        author_field = meta.get("title")
                    elif final_platform == "Bloomberg":
                        author_field = meta.get("title")

                    if author_field:
                        final_username = author_field

                    category = extract_category_keywords(
                        metadata_json, final_platform, url_type
                    )
                else:
                    category = "N/A (details unavailable)"

                detailed_live_streams.append(
                    {
                        "url": url,
                        "alias": url_to_alias_map.get(url),
                        "username": final_username,
                        "platform": final_platform,
                        "category_keywords": category,
                        "viewer_count": viewer_count,  # <<<< ADD THIS NEW KEY
                        "is_live": True,
                    }
                )
            except FileNotFoundError as e:
                logger.critical(
                    f"streamlink command not found during metadata fetch for {url}"
                )
                raise  # Propagate critical streamlink error
            except Exception as e:
                logger.exception(f"Error fetching metadata for {url}")
                # Fallback: add with basic info if metadata fetch failed but was initially live
                detailed_live_streams.append(
                    {
                        "url": url,
                        "alias": url_to_alias_map.get(url),
                        "username": initial_username,
                        "platform": initial_platform,
                        "category_keywords": f"N/A (err: {str(e)[:20]})",
                        "viewer_count": None,  # <<<< ADD THIS NEW KEY
                        "is_live": True,
                    }
                )

    # Sort the detailed_live_streams list to match the order of live_stream_candidates
    ordered_final_streams = []
    url_to_details_map = {s["url"]: s for s in detailed_live_streams}
    for url in all_configured_urls:
        if url in url_to_details_map:
            ordered_final_streams.append(url_to_details_map[url])

    return ordered_final_streams
