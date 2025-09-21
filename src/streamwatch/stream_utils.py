import re
from typing import Dict
from urllib.parse import urlparse

from .models import UrlMetadata, UrlType


def _result(platform: str, username: str, url_type: str = "unknown") -> Dict[str, str]:
    """Create a consistent result structure for URL parsing."""
    return {"platform": platform, "username": username, "type": url_type}


def parse_url_metadata(url: str) -> Dict[str, str]:
    """
    Parses a stream URL to extract platform, a preliminary username/ID, and URL type.
    """
    if (
        not isinstance(url, str)
        or not url.strip()
        or not url.lower().startswith(("http://", "https://"))
    ):
        return _result("Unknown", "unknown_stream", "parse_error")

    try:
        parsed_uri = urlparse(url)
        netloc = parsed_uri.netloc.replace("www.", "")
        path = parsed_uri.path
    except ValueError:
        return _result("Unknown", "unknown_stream", "parse_error")

    # --- Platform-Specific Parsing ---

    # Twitch
    if "twitch.tv" in netloc:
        m = re.match(r"/([a-zA-Z0-9_]{4,25})/?$", path)
        if m:
            return _result("Twitch", m.group(1), "channel")
        return _result("Twitch", "unknown_user", "parse_error")

    # YouTube
    if "youtube.com" in netloc or "youtu.be" in netloc:
        # Match channel URLs (@handle, /c/, /channel/, /user/)
        channel_match = re.match(
            r"/(?:@([a-zA-Z0-9_.-]+)|c/([a-zA-Z0-9_.-]+)|channel/([a-zA-Z0-9_-]+)|user/([a-zA-Z0-9_.-]+))/?",
            path,
        )
        if channel_match:
            username = next(
                (g for g in channel_match.groups() if g is not None), "unknown_channel"
            )
            return _result("YouTube", username, "channel")

        # Match video URLs (/watch?v= or youtu.be/)
        video_id_match = re.search(r"(?:/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
        if video_id_match:
            return _result("YouTube", video_id_match.group(1), "video")

        return _result("YouTube", "unknown_youtube_url", "parse_error")

    # Kick
    if "kick.com" in netloc:
        m = re.match(r"/([a-zA-Z0-9_]+)/?$", path)
        if m:
            return _result("Kick", m.group(1), "channel")
        return _result("Kick", "unknown_user", "parse_error")

    # --- Generic Fallback ---
    try:
        # More robustly find the main domain part
        domain_parts = netloc.split(".")
        platform_name = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
    except IndexError:
        platform_name = "Unknown"

    path_parts = [part for part in path.split("/") if part]
    if path_parts:
        username_guess = path_parts[-1]
    else:
        username_guess = netloc  # Fallback to the domain itself

    return _result(platform_name, username_guess, "generic_fallback")


def parse_url_metadata_typed(url: str) -> UrlMetadata:
    """
    Parses a stream URL to extract platform, username, and URL type with type safety.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    result_dict = parse_url_metadata(url)

    try:
        url_type = UrlType(result_dict["type"])
    except ValueError:
        url_type = UrlType.UNKNOWN

    return UrlMetadata(
        platform=result_dict["platform"],
        username=result_dict["username"],
        url_type=url_type,
    )
