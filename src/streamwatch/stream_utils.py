# src/streamwatch/stream_utils.py
import re
from urllib.parse import urlparse

# Helper to create a consistent result structure
def _result(platform, username, url_type="unknown"):
    return {'platform': platform, 'username': username, 'type': url_type}

def parse_url_metadata(url):
    """
    Parses a stream URL to extract platform, a preliminary username/ID, and URL type.
    """
    # --- FINAL, ROBUST VALIDATION CHECK ---
    # 1. Check if it's a non-empty string.
    # 2. Check if it starts with 'http://' or 'https://' (case-insensitive).
    if not isinstance(url, str) or not url.strip() or not url.lower().startswith(('http://', 'https://')):
        # This single line handles:
        # - Non-string inputs
        # - Empty strings
        # - Strings that don't look like web URLs (e.g., "not a url")
        # - URLs with other schemes (e.g., "ftp://...")
        return _result('Unknown', 'unknown_stream', 'parse_error')

    # --- Platform-Specific Parsing using urlparse ---
    try:
        parsed_uri = urlparse(url)
        # Normalize netloc by removing 'www.' if it exists at the start
        netloc = parsed_uri.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]
    except ValueError: # Catches malformed URLs that slip past the initial check
        return _result('Unknown', 'unknown_stream', 'parse_error')

    # Routing based on domain
    if 'twitch.tv' in netloc:
        m = re.match(r"/([a-zA-Z0-9_]+)/?$", parsed_uri.path)
        if m: return _result('Twitch', m.group(1), 'channel')
        return _result('Twitch', 'unknown_user', 'parse_error')

    if 'youtube.com' in netloc:
        m = re.match(r"/(?:@([a-zA-Z0-9_.-]+)|channel/([a-zA-Z0-9_-]+)|c/([a-zA-Z0-9_.-]+)|user/([a-zA-Z0-9_.-]+))/?", parsed_uri.path)
        if m: return _result('YouTube', m.group(1) or m.group(2) or m.group(3) or m.group(4), 'channel')
        
        # Correctly handle /watch and /live paths
        path_match = re.match(r"/(live/([a-zA-Z0-9_-]+)|watch)/?", parsed_uri.path)
        if path_match:
            video_id = path_match.group(2) # This is for /live/VIDEO_ID
            if not video_id and path_match.group(1) == 'watch' and parsed_uri.query: # This is for /watch?v=...
                # Simple query parsing
                query_params = dict(p.split('=', 1) for p in parsed_uri.query.split('&') if '=' in p)
                video_id = query_params.get('v')
            
            if video_id:
                return _result('YouTube', video_id, 'video')
        return _result('YouTube', 'unknown_video', 'parse_error')

    # --- (The rest of your specific platform checks can remain here as they are) ---
    if 'kick.com' in netloc:
        m = re.match(r"/([a-zA-Z0-9_]+)/?$", parsed_uri.path)
        if m: return _result('Kick', m.group(1), 'channel')
        return _result('Kick', 'unknown_user', 'parse_error')
        
    if 'bbc.co.uk' in netloc:
        m = re.match(r"/iplayer/live/([a-zA-Z0-9_]+)/?$", parsed_uri.path)
        if m: return _result('BBC iPlayer', m.group(1), 'channel_id')
    
    if 'zdf.de' in netloc:
        m = re.match(r"/live-tv(?:/([a-zA-Z0-9_-]+))?/?$", parsed_uri.path)
        if m: return _result('ZDF Mediathek', m.group(1) or "zdf", 'channel_id')

    # ... and so on for your other platforms ...

    # --- Generic Fallback (If no specific domain matched) ---
    domain_parts = netloc.split('.')
    platform_name = domain_parts[-2] if len(domain_parts) >= 2 else domain_parts[0]
    platform_name = platform_name.capitalize()

    path_parts = [part for part in parsed_uri.path.split('/') if part]
    if path_parts:
        username_guess = path_parts[-1]
        if username_guess.lower() in ['live', 'channel', 'streams', 'videos'] and len(path_parts) > 1:
            username_guess = path_parts[-2]
        return _result(platform_name, username_guess, 'generic_fallback')
    else: # No path, e.g., https://somesite.com/
        return _result(platform_name, 'stream', 'generic_fallback')