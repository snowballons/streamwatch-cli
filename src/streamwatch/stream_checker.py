import json  # For parsing --json output
import logging  # Import logging
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Union

from . import config
from .exceptions import (
    StreamlinkError, StreamNotFoundError, NetworkError,
    AuthenticationError, TimeoutError, categorize_streamlink_error
)
from .models import StreamInfo, StreamMetadata, StreamStatus
from .resilience import (
    RetryConfig, CircuitBreakerConfig, resilient_operation,
    get_circuit_breaker, CircuitBreakerOpenError
)
from .stream_utils import parse_url_metadata  # IMPORT THE NEW FUNCTION

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".stream_checker")


def _get_retry_config() -> RetryConfig:
    """Get retry configuration from app config."""
    return RetryConfig(
        max_attempts=config.get_retry_max_attempts(),
        base_delay=config.get_retry_base_delay(),
        max_delay=config.get_retry_max_delay(),
        exponential_base=config.get_retry_exponential_base(),
        jitter=config.get_retry_jitter()
    )


def _get_circuit_breaker_config() -> CircuitBreakerConfig:
    """Get circuit breaker configuration from app config."""
    return CircuitBreakerConfig(
        failure_threshold=config.get_circuit_breaker_failure_threshold(),
        recovery_timeout=config.get_circuit_breaker_recovery_timeout(),
        success_threshold=config.get_circuit_breaker_success_threshold()
    )


class StreamCheckResult:
    """
    Represents the result of a stream liveness check with detailed error information.
    """

    def __init__(self, is_live: bool, url: str, error: Optional[StreamlinkError] = None):
        """
        Initialize StreamCheckResult.

        Args:
            is_live: Whether the stream is live
            url: The stream URL that was checked
            error: Detailed error information if check failed
        """
        self.is_live = is_live
        self.url = url
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for structured logging/debugging."""
        result = {
            'is_live': self.is_live,
            'url': self.url
        }
        if self.error:
            result['error'] = self.error.to_dict()
        return result


class MetadataResult:
    """
    Represents the result of a stream metadata fetch with detailed error information.
    """

    def __init__(self, success: bool, url: str, json_data: Optional[str] = None,
                 error: Optional[StreamlinkError] = None):
        """
        Initialize MetadataResult.

        Args:
            success: Whether the metadata fetch was successful
            url: The stream URL that was processed
            json_data: The JSON metadata string if successful
            error: Detailed error information if fetch failed
        """
        self.success = success
        self.url = url
        self.json_data = json_data
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for structured logging/debugging."""
        result = {
            'success': self.success,
            'url': self.url,
            'has_json_data': self.json_data is not None
        }
        if self.error:
            result['error'] = self.error.to_dict()
        return result


def is_stream_live_for_check(url: str) -> Tuple[bool, str]:
    """
    Checks if a given stream URL is currently live using streamlink.

    This is a backward-compatible wrapper around is_stream_live_for_check_detailed
    for existing code that expects the old return format.

    Args:
        url: The stream URL to check

    Returns:
        Tuple of (is_live, url)
    """
    result = is_stream_live_for_check_detailed(url)
    return result.is_live, result.url


def _is_stream_live_core(url: str) -> StreamCheckResult:
    """
    Core implementation for checking if a stream URL is live.
    This is the base function without resilience patterns.

    Args:
        url: The stream URL to check

    Returns:
        StreamCheckResult: Detailed result with error categorization
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
            return StreamCheckResult(is_live=True, url=url)

        # Stream is not live or error occurred - categorize the error
        error = categorize_streamlink_error(
            stderr=process.stderr or "",
            stdout=process.stdout or "",
            return_code=process.returncode,
            url=url
        )

        # Log appropriate level based on error type
        if isinstance(error, StreamNotFoundError):
            logger.info(f"Stream is not live: {url} - {error}")
        elif isinstance(error, (NetworkError, AuthenticationError)):
            logger.warning(f"Stream check failed: {url} - {error}")
        else:
            logger.warning(f"Ambiguous liveness result for: {url} - {error}")

        return StreamCheckResult(is_live=False, url=url, error=error)

    except subprocess.TimeoutExpired:
        error = TimeoutError(
            f"Timeout expired checking liveness for: {url}",
            url=url
        )
        logger.warning(f"Timeout expired checking liveness for: {url}")
        return StreamCheckResult(is_live=False, url=url, error=error)

    except FileNotFoundError:
        logger.critical("streamlink command not found during check.")
        raise FileNotFoundError("streamlink command not found during check.")

    except Exception as e:
        # Wrap unexpected exceptions in StreamlinkError
        error = StreamlinkError(
            f"Unexpected error checking liveness: {str(e)}",
            url=url
        )
        logger.exception(f"Error checking liveness for {url}")
        return StreamCheckResult(is_live=False, url=url, error=error)


def is_stream_live_for_check_detailed(url: str) -> StreamCheckResult:
    """
    Checks if a given stream URL is currently live using streamlink with detailed error information
    and resilience patterns (retry logic and circuit breaker).

    Args:
        url: The stream URL to check

    Returns:
        StreamCheckResult: Detailed result with error categorization
    """
    if not config.get_circuit_breaker_enabled():
        # If resilience is disabled, use the core function directly
        return _is_stream_live_core(url)

    try:
        # Use resilient operation with retry and circuit breaker
        @resilient_operation(
            operation_name=f"stream_liveness_check_{url}",
            retry_config=_get_retry_config(),
            circuit_breaker_config=_get_circuit_breaker_config(),
            use_circuit_breaker=True
        )
        def resilient_check():
            result = _is_stream_live_core(url)
            # If the result indicates an error that should trigger circuit breaker,
            # raise the exception to be handled by resilience patterns
            if result.error and isinstance(result.error, (NetworkError, TimeoutError)):
                raise result.error
            return result

        return resilient_check()

    except CircuitBreakerOpenError as e:
        # Circuit breaker is open - return a specific error
        error = NetworkError(
            f"Circuit breaker open for stream checks: {str(e)}",
            url=url
        )
        logger.warning(f"Circuit breaker open for stream liveness check: {url}")
        return StreamCheckResult(is_live=False, url=url, error=error)

    except Exception as e:
        # Handle any other exceptions from resilience patterns
        if isinstance(e, StreamlinkError):
            return StreamCheckResult(is_live=False, url=url, error=e)
        else:
            error = StreamlinkError(f"Resilience pattern error: {str(e)}", url=url)
            return StreamCheckResult(is_live=False, url=url, error=error)


def get_stream_metadata_json(url: str) -> Tuple[bool, str]:
    """
    Fetches stream metadata using streamlink --json.

    This is a backward-compatible wrapper around get_stream_metadata_json_detailed
    for existing code that expects the old return format.

    Args:
        url: The stream URL to get metadata for

    Returns:
        Tuple of (success, json_string_or_error_message)
    """
    try:
        result = get_stream_metadata_json_detailed(url)
        if result.success:
            return (True, result.json_data)
        else:
            return (False, str(result.error) if result.error else "Unknown error")
    except Exception as e:
        return (False, str(e))


def _get_stream_metadata_core(url: str) -> 'MetadataResult':
    """
    Core implementation for fetching stream metadata.
    This is the base function without resilience patterns.

    Args:
        url: The stream URL to get metadata for

    Returns:
        MetadataResult: Detailed result with error categorization
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
                # Validate JSON format
                json.loads(process.stdout)  # This will raise if invalid JSON
                return MetadataResult(success=True, json_data=process.stdout, url=url)
            except json.JSONDecodeError as e:
                error = StreamlinkError(
                    f"Invalid JSON response: {str(e)}",
                    url=url, stdout=process.stdout, stderr=process.stderr,
                    return_code=process.returncode
                )
                logger.warning(f"Could not process JSON for {url}: {e}")
                return MetadataResult(success=False, url=url, error=error)

        # Metadata fetch failed - categorize the error
        error = categorize_streamlink_error(
            stderr=process.stderr or "",
            stdout=process.stdout or "",
            return_code=process.returncode,
            url=url
        )

        logger.warning(f"streamlink --json for {url} failed - {error}")
        return MetadataResult(success=False, url=url, error=error)

    except subprocess.TimeoutExpired:
        error = TimeoutError(
            f"Timeout fetching JSON metadata for {url}",
            url=url
        )
        logger.warning(f"Timeout fetching JSON metadata for {url}")
        return MetadataResult(success=False, url=url, error=error)

    except FileNotFoundError:
        logger.critical("streamlink command not found during JSON metadata fetch.")
        raise FileNotFoundError(
            "streamlink command not found during JSON metadata fetch."
        )
    except Exception as e:
        # Wrap unexpected exceptions in StreamlinkError
        error = StreamlinkError(
            f"Unexpected error fetching metadata: {str(e)}",
            url=url
        )
        logger.exception(f"Error fetching JSON metadata for {url}")
        return MetadataResult(success=False, url=url, error=error)


def get_stream_metadata_json_detailed(url: str) -> 'MetadataResult':
    """
    Fetches stream metadata using streamlink --json with detailed error information
    and resilience patterns (retry logic and circuit breaker).

    Args:
        url: The stream URL to get metadata for

    Returns:
        MetadataResult: Detailed result with error categorization
    """
    if not config.get_circuit_breaker_enabled():
        # If resilience is disabled, use the core function directly
        return _get_stream_metadata_core(url)

    try:
        # Use resilient operation with retry and circuit breaker
        @resilient_operation(
            operation_name=f"stream_metadata_fetch_{url}",
            retry_config=_get_retry_config(),
            circuit_breaker_config=_get_circuit_breaker_config(),
            use_circuit_breaker=True
        )
        def resilient_fetch():
            result = _get_stream_metadata_core(url)
            # If the result indicates an error that should trigger circuit breaker,
            # raise the exception to be handled by resilience patterns
            if not result.success and result.error and isinstance(result.error, (NetworkError, TimeoutError)):
                raise result.error
            return result

        return resilient_fetch()

    except CircuitBreakerOpenError as e:
        # Circuit breaker is open - return a specific error
        error = NetworkError(
            f"Circuit breaker open for metadata fetch: {str(e)}",
            url=url
        )
        logger.warning(f"Circuit breaker open for metadata fetch: {url}")
        return MetadataResult(success=False, url=url, error=error)

    except Exception as e:
        # Handle any other exceptions from resilience patterns
        if isinstance(e, StreamlinkError):
            return MetadataResult(success=False, url=url, error=e)
        else:
            error = StreamlinkError(f"Resilience pattern error: {str(e)}", url=url)
            return MetadataResult(success=False, url=url, error=error)


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
