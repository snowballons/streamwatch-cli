import json  # For parsing --json output
import logging  # Import logging
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Union

from . import config
from .cache import get_cache
from .exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitExceededError,
    StreamlinkError,
    StreamNotFoundError,
    TimeoutError,
    categorize_streamlink_error,
)
from .models import StreamInfo, StreamMetadata, StreamStatus
from .rate_limiter import get_rate_limiter
from .resilience import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    RetryConfig,
    get_circuit_breaker,
    resilient_operation,
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
        jitter=config.get_retry_jitter(),
    )


def _get_circuit_breaker_config() -> CircuitBreakerConfig:
    """Get circuit breaker configuration from app config."""
    return CircuitBreakerConfig(
        failure_threshold=config.get_circuit_breaker_failure_threshold(),
        recovery_timeout=config.get_circuit_breaker_recovery_timeout(),
        success_threshold=config.get_circuit_breaker_success_threshold(),
    )


class StreamCheckResult:
    """
    Represents the result of a stream liveness check with detailed error information.
    """

    def __init__(
        self, is_live: bool, url: str, error: Optional[StreamlinkError] = None
    ):
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
        result = {"is_live": self.is_live, "url": self.url}
        if self.error:
            result["error"] = self.error.to_dict()
        return result


class MetadataResult:
    """
    Represents the result of a stream metadata fetch with detailed error information.
    """

    def __init__(
        self,
        success: bool,
        url: str,
        json_data: Optional[str] = None,
        error: Optional[StreamlinkError] = None,
    ):
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
            "success": self.success,
            "url": self.url,
            "has_json_data": self.json_data is not None,
        }
        if self.error:
            result["error"] = self.error.to_dict()
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
            url=url,
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
        error = TimeoutError(f"Timeout expired checking liveness for: {url}", url=url)
        logger.warning(f"Timeout expired checking liveness for: {url}")
        return StreamCheckResult(is_live=False, url=url, error=error)

    except FileNotFoundError:
        logger.critical("streamlink command not found during check.")
        raise FileNotFoundError("streamlink command not found during check.")

    except Exception as e:
        # Wrap unexpected exceptions in StreamlinkError
        error = StreamlinkError(
            f"Unexpected error checking liveness: {str(e)}", url=url
        )
        logger.exception(f"Error checking liveness for {url}")
        return StreamCheckResult(is_live=False, url=url, error=error)


def is_stream_live_for_check_detailed(url: str) -> StreamCheckResult:
    """
    Checks if a given stream URL is currently live using streamlink with detailed error information,
    resilience patterns (retry logic and circuit breaker), caching, and rate limiting.

    Args:
        url: The stream URL to check

    Returns:
        StreamCheckResult: Detailed result with error categorization
    """
    # Check cache first if caching is enabled
    if config.get_cache_enabled():
        cache = get_cache()
        cached_status = cache.get(url)
        if cached_status is not None:
            logger.debug(f"Using cached status for {url}: {cached_status.value}")
            # Convert cached status to StreamCheckResult
            is_live = cached_status == StreamStatus.LIVE
            return StreamCheckResult(is_live=is_live, url=url)

    # Apply rate limiting before making streamlink call
    if config.get_rate_limit_enabled():
        rate_limiter = get_rate_limiter()
        timeout = (
            config.get_streamlink_timeout_liveness()
        )  # Use streamlink timeout as rate limit timeout

        if not rate_limiter.acquire(url, timeout=timeout):
            # Rate limit exceeded
            from .stream_utils import parse_url_metadata

            platform = parse_url_metadata(url).get("platform", "Unknown")
            error = RateLimitExceededError(
                f"Rate limit exceeded for {platform}", url=url, platform=platform
            )
            logger.warning(f"Rate limit exceeded for {url}")
            return StreamCheckResult(is_live=False, url=url, error=error)

    # Cache miss or caching disabled - perform actual check
    if not config.get_circuit_breaker_enabled():
        # If resilience is disabled, use the core function directly
        result = _is_stream_live_core(url)
    else:
        try:
            # Use resilient operation with retry and circuit breaker
            @resilient_operation(
                operation_name=f"stream_liveness_check_{url}",
                retry_config=_get_retry_config(),
                circuit_breaker_config=_get_circuit_breaker_config(),
                use_circuit_breaker=True,
            )
            def resilient_check():
                result = _is_stream_live_core(url)
                # If the result indicates an error that should trigger circuit breaker,
                # raise the exception to be handled by resilience patterns
                if result.error and isinstance(
                    result.error, (NetworkError, TimeoutError)
                ):
                    raise result.error
                return result

            result = resilient_check()

        except CircuitBreakerOpenError as e:
            # Circuit breaker is open - return a specific error
            error = NetworkError(
                f"Circuit breaker open for stream checks: {str(e)}", url=url
            )
            logger.warning(f"Circuit breaker open for stream liveness check: {url}")
            result = StreamCheckResult(is_live=False, url=url, error=error)

        except Exception as e:
            # Handle any other exceptions from resilience patterns
            if isinstance(e, StreamlinkError):
                result = StreamCheckResult(is_live=False, url=url, error=e)
            else:
                error = StreamlinkError(f"Resilience pattern error: {str(e)}", url=url)
                result = StreamCheckResult(is_live=False, url=url, error=error)

    # Update cache with the result if caching is enabled
    if config.get_cache_enabled():
        cache = get_cache()
        # Determine status to cache based on result
        if result.is_live:
            status = StreamStatus.LIVE
        elif result.error and isinstance(result.error, StreamNotFoundError):
            status = StreamStatus.OFFLINE
        elif result.error:
            status = StreamStatus.ERROR
        else:
            status = StreamStatus.OFFLINE

        cache.put(url, status)
        logger.debug(f"Cached status for {url}: {status.value}")

    return result


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


def _get_stream_metadata_core(url: str) -> "MetadataResult":
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
                    url=url,
                    stdout=process.stdout,
                    stderr=process.stderr,
                    return_code=process.returncode,
                )
                logger.warning(f"Could not process JSON for {url}: {e}")
                return MetadataResult(success=False, url=url, error=error)

        # Metadata fetch failed - categorize the error
        error = categorize_streamlink_error(
            stderr=process.stderr or "",
            stdout=process.stdout or "",
            return_code=process.returncode,
            url=url,
        )

        logger.warning(f"streamlink --json for {url} failed - {error}")
        return MetadataResult(success=False, url=url, error=error)

    except subprocess.TimeoutExpired:
        error = TimeoutError(f"Timeout fetching JSON metadata for {url}", url=url)
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
            f"Unexpected error fetching metadata: {str(e)}", url=url
        )
        logger.exception(f"Error fetching JSON metadata for {url}")
        return MetadataResult(success=False, url=url, error=error)


def get_stream_metadata_json_detailed(url: str) -> "MetadataResult":
    """
    Fetches stream metadata using streamlink --json with detailed error information,
    resilience patterns (retry logic and circuit breaker), and rate limiting.

    Args:
        url: The stream URL to get metadata for

    Returns:
        MetadataResult: Detailed result with error categorization
    """
    # Apply rate limiting before making streamlink call
    if config.get_rate_limit_enabled():
        rate_limiter = get_rate_limiter()
        timeout = (
            config.get_streamlink_timeout_metadata()
        )  # Use metadata timeout as rate limit timeout

        if not rate_limiter.acquire(url, timeout=timeout):
            # Rate limit exceeded
            from .stream_utils import parse_url_metadata

            platform = parse_url_metadata(url).get("platform", "Unknown")
            error = RateLimitExceededError(
                f"Rate limit exceeded for {platform} metadata fetch",
                url=url,
                platform=platform,
            )
            logger.warning(f"Rate limit exceeded for metadata fetch: {url}")
            return MetadataResult(success=False, url=url, error=error)

    if not config.get_circuit_breaker_enabled():
        # If resilience is disabled, use the core function directly
        return _get_stream_metadata_core(url)

    try:
        # Use resilient operation with retry and circuit breaker
        @resilient_operation(
            operation_name=f"stream_metadata_fetch_{url}",
            retry_config=_get_retry_config(),
            circuit_breaker_config=_get_circuit_breaker_config(),
            use_circuit_breaker=True,
        )
        def resilient_fetch():
            result = _get_stream_metadata_core(url)
            # If the result indicates an error that should trigger circuit breaker,
            # raise the exception to be handled by resilience patterns
            if (
                not result.success
                and result.error
                and isinstance(result.error, (NetworkError, TimeoutError))
            ):
                raise result.error
            return result

        return resilient_fetch()

    except CircuitBreakerOpenError as e:
        # Circuit breaker is open - return a specific error
        error = NetworkError(
            f"Circuit breaker open for metadata fetch: {str(e)}", url=url
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
    all_configured_streams_data: List[Dict[str, str]],
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

    logger.info(f"Found {len(live_stream_candidates)} potentially live stream(s).")
    logger.info("Fetching stream metadata...")

    # Phase 2: Fetch metadata for live streams
    live_streams_info = []
    url_to_details_map = {s["url"]: s for s in all_configured_streams_data}
    
    with ThreadPoolExecutor(max_workers=config.get_max_workers_metadata()) as executor:
        future_to_url = {
            executor.submit(get_stream_metadata_json, url): url
            for url in live_stream_candidates
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            success, json_data = future.result()
            
            if url in url_to_details_map:
                stream_data = url_to_details_map[url]
                
                # Extract category/title from metadata
                category = "N/A"
                viewer_count = None
                title = None
                
                if success and json_data:
                    try:
                        import json
                        metadata_json = json.loads(json_data)
                        if "metadata" in metadata_json:
                            meta = metadata_json["metadata"]
                            title = meta.get("title")
                            
                            # Extract viewer count
                            for key in ["viewers", "viewer_count", "online"]:
                                if key in meta and meta[key] is not None:
                                    try:
                                        viewer_count = int(meta[key])
                                        if viewer_count >= 0:
                                            break
                                    except (ValueError, TypeError):
                                        continue
                            
                            # Extract category using existing logic
                            platform = stream_data.get("platform", "Unknown")
                            category = extract_category_keywords((success, json_data), platform)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Could not parse metadata for {url}: {e}")
                
                live_streams_info.append(
                    StreamInfo(
                        url=url,
                        alias=stream_data.get("alias", "Unnamed"),
                        platform=stream_data.get("platform", "Unknown"),
                        username=stream_data.get("username", "unknown"),
                        category=category,
                        title=title,
                        viewer_count=viewer_count,
                        status=StreamStatus.LIVE,
                    )
                )

    # Return the list of enhanced objects, converted to dictionaries for compatibility
    return [s.model_dump() for s in live_streams_info]


# --- Cache Management Functions ---


def clear_stream_cache() -> int:
    """
    Clear all cached stream status entries.

    Returns:
        Number of entries cleared
    """
    if not config.get_cache_enabled():
        logger.info("Cache is disabled, nothing to clear")
        return 0

    cache = get_cache()
    count = cache.clear()
    logger.info(f"Cleared {count} cached stream status entries")
    return count


def invalidate_stream_cache(url: str) -> bool:
    """
    Invalidate cache entry for a specific stream URL.

    Args:
        url: The stream URL to invalidate

    Returns:
        True if entry was removed, False if not found
    """
    if not config.get_cache_enabled():
        logger.debug("Cache is disabled, nothing to invalidate")
        return False

    cache = get_cache()
    result = cache.invalidate(url)
    if result:
        logger.debug(f"Invalidated cache entry for: {url}")
    return result


def cleanup_expired_cache() -> int:
    """
    Remove expired entries from the stream cache.

    Returns:
        Number of expired entries removed
    """
    if not config.get_cache_enabled():
        return 0

    cache = get_cache()
    count = cache.cleanup_expired()
    if count > 0:
        logger.debug(f"Cleaned up {count} expired cache entries")
    return count


def get_cache_stats() -> Dict[str, int]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    if not config.get_cache_enabled():
        return {"total_entries": 0, "active_entries": 0, "expired_entries": 0}

    cache = get_cache()
    return cache.get_stats()


# --- Rate Limiting Management Functions ---


def get_rate_limit_status() -> Dict[str, Dict[str, float]]:
    """
    Get rate limiting status for all platforms.

    Returns:
        Dictionary with rate limiting status for global and platform limiters
    """
    if not config.get_rate_limit_enabled():
        return {}

    rate_limiter = get_rate_limiter()
    return rate_limiter.get_status()


def check_rate_limit_available(url: str) -> bool:
    """
    Check if a request can proceed immediately without rate limiting.

    Args:
        url: The stream URL to check

    Returns:
        True if request can proceed immediately, False if rate limited
    """
    if not config.get_rate_limit_enabled():
        return True

    rate_limiter = get_rate_limiter()
    return rate_limiter.try_acquire(url)


def reset_rate_limiters() -> None:
    """
    Reset all rate limiters (mainly for testing and debugging).
    """
    from .rate_limiter import reset_rate_limiter

    reset_rate_limiter()
    logger.info("Reset all rate limiters")


def get_rate_limit_status_message() -> str:
    """
    Get a human-readable rate limit status message for UI display.

    Returns:
        String describing current rate limit status
    """
    if not config.get_rate_limit_enabled():
        return ""

    try:
        status = get_rate_limit_status()
        if not status:
            return ""

        messages = []

        # Global status
        if "global" in status:
            global_status = status["global"]
            utilization = global_status["utilization"]
            if utilization > 0.7:  # High utilization
                messages.append(
                    f"Rate limiting active (Global: {utilization:.0%} used)"
                )

        # Platform status - only show if heavily utilized
        for platform, platform_status in status.items():
            if platform == "global":
                continue
            utilization = platform_status["utilization"]
            if utilization > 0.8:  # Very high utilization
                messages.append(
                    f"{platform.title()}: {utilization:.0%} rate limit used"
                )

        if messages:
            return "⏳ " + ", ".join(messages)

        return ""

    except Exception as e:
        logger.debug(f"Error getting rate limit status message: {e}")
        return ""
