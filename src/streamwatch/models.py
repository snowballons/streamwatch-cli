"""
Data models for StreamWatch application.

This module defines the core data structures used throughout the application
using dataclasses for type safety and validation.
"""

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class StreamStatus(Enum):
    """Enumeration of possible stream statuses."""

    LIVE = "live"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    ERROR = "error"


class UrlType(Enum):
    """Enumeration of URL types for stream parsing."""

    CHANNEL = "channel"
    VIDEO = "video"
    CHANNEL_ID = "channel_id"
    GENERIC_FALLBACK = "generic_fallback"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"


class PlaybackAction(Enum):
    """Enumeration of playback session actions."""

    RETURN_TO_MAIN = "return_to_main"
    QUIT_APPLICATION = "quit_application"
    STOP_PLAYBACK = "stop_playback"
    CONTINUE = "continue"


@dataclass
class UrlMetadata:
    """Metadata extracted from a stream URL."""

    platform: str
    username: str
    url_type: UrlType = UrlType.UNKNOWN

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for backward compatibility."""
        return {
            "platform": self.platform,
            "username": self.username,
            "type": self.url_type.value,
        }


@dataclass
class StreamInfo:
    """Complete information about a stream."""

    url: str
    alias: str
    platform: str = "Unknown"
    username: str = "unknown_stream"
    category: str = "N/A"
    viewer_count: Optional[int] = None
    status: StreamStatus = StreamStatus.UNKNOWN
    url_type: UrlType = UrlType.UNKNOWN

    def __post_init__(self) -> None:
        """Validate and normalize data after initialization."""
        if not self.url.strip():
            raise ValueError("URL cannot be empty")
        if not self.alias.strip():
            raise ValueError("Alias cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        return {
            "url": self.url,
            "alias": self.alias,
            "platform": self.platform,
            "username": self.username,
            "category": self.category,
            "viewer_count": self.viewer_count,
            "status": self.status.value
            if isinstance(self.status, StreamStatus)
            else self.status,
            "url_type": self.url_type.value
            if isinstance(self.url_type, UrlType)
            else self.url_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamInfo":
        """Create StreamInfo from dictionary data."""
        # Handle legacy data that might not have all fields
        status = data.get("status", StreamStatus.UNKNOWN.value)
        if isinstance(status, str):
            try:
                status = StreamStatus(status)
            except ValueError:
                status = StreamStatus.UNKNOWN

        url_type = data.get("url_type", UrlType.UNKNOWN.value)
        if isinstance(url_type, str):
            try:
                url_type = UrlType(url_type)
            except ValueError:
                url_type = UrlType.UNKNOWN

        return cls(
            url=data["url"],
            alias=data.get("alias", "Unnamed Stream"),
            platform=data.get("platform", "Unknown"),
            username=data.get("username", "unknown_stream"),
            category=data.get("category", "N/A"),
            viewer_count=data.get("viewer_count"),
            status=status,
            url_type=url_type,
        )


@dataclass
class PlaybackSession:
    """Represents an active playback session."""

    current_stream: StreamInfo
    current_quality: str
    all_live_streams: List[StreamInfo]
    player_process: Optional[subprocess.Popen] = None
    current_index: int = 0
    user_intent_direction: int = 0  # 0: none, 1: next, -1: previous

    def __post_init__(self) -> None:
        """Initialize session state after creation."""
        # Find current stream index in the live streams list
        try:
            self.current_index = next(
                idx
                for idx, stream in enumerate(self.all_live_streams)
                if stream.url == self.current_stream.url
            )
        except StopIteration:
            self.current_index = 0

    def get_next_stream(self) -> Optional[StreamInfo]:
        """Get the next stream in the list."""
        if not self.all_live_streams:
            return None
        next_index = (self.current_index + 1) % len(self.all_live_streams)
        return self.all_live_streams[next_index]

    def get_previous_stream(self) -> Optional[StreamInfo]:
        """Get the previous stream in the list."""
        if not self.all_live_streams:
            return None
        prev_index = (self.current_index - 1) % len(self.all_live_streams)
        return self.all_live_streams[prev_index]


@dataclass
class StreamMetadata:
    """Metadata from streamlink JSON output."""

    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    viewer_count: Optional[int] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, json_data: Optional[Dict[str, Any]]) -> "StreamMetadata":
        """Create StreamMetadata from streamlink JSON output."""
        if not json_data or "metadata" not in json_data:
            return cls()

        meta = json_data["metadata"]

        # Extract viewer count from various possible keys
        viewer_count = None
        for key in ["viewers", "viewer_count", "online"]:
            if key in meta and meta[key] is not None:
                try:
                    viewer_count = int(meta[key])
                    break
                except (ValueError, TypeError):
                    continue

        return cls(
            title=meta.get("title"),
            author=meta.get("author"),
            category=meta.get("category"),
            viewer_count=viewer_count,
            raw_metadata=meta,
        )


@dataclass
class ConfigSection:
    """Represents a configuration section with typed access."""

    section_name: str
    values: Dict[str, str] = field(default_factory=dict)

    def get_str(self, key: str, default: str = "") -> str:
        """Get string value with default."""
        return self.values.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer value with default."""
        try:
            return int(self.values.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value with default."""
        value = self.values.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
