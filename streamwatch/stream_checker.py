import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import json # For parsing --json output
import sys
import logging # Import logging
from . import config
from .stream_utils import parse_url_metadata # IMPORT THE NEW FUNCTION
import re

# Get a logger for this module
logger = logging.getLogger(config.APP_NAME + ".stream_checker")

def is_stream_live_for_check(url):
    """
    Checks if a given stream URL is currently live using streamlink.
    Returns a tuple: (bool_is_live, url)
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
            check=False
        )
        if process.returncode == 0 and "Available streams:" in process.stdout:
            logger.debug(f"Stream is live: {url}")
            return True, url

        stderr_lower = process.stderr.lower()
        stdout_lower = process.stdout.lower()
        if "no playable streams found" in stderr_lower or \
           "error: no streams found on" in stderr_lower or \
           "this stream is offline" in stdout_lower or \
           process.returncode != 0:
            logger.info(f"Stream is not live: {url}")
            return False, url
        logger.warning(f"Ambiguous liveness result for: {url}")
        return False, url # Default to not live for ambiguous cases
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout expired checking liveness for: {url}")
        return False, url
    except FileNotFoundError:
        logger.critical("streamlink command not found during check.")
        raise FileNotFoundError("streamlink command not found during check.")
    except Exception as e: # Catch any other exception during the check for a single stream
        logger.exception(f"Error checking liveness for {url}")
        return False, url

def get_stream_metadata_json(url):
    """Fetches stream metadata using streamlink --json."""
    command = ["streamlink", "--twitch-disable-ads", url, "--json"]
    if config.get_twitch_disable_ads() and "twitch.tv" in url: # Ensure flag is relevant
        pass # Already included --twitch-disable-ads
    elif "--twitch-disable-ads" in command and "twitch.tv" not in url:
        command.remove("--twitch-disable-ads")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=config.get_streamlink_timeout_metadata(),  # Slightly longer timeout for JSON
            check=False # Don't crash on non-zero, parse stderr
        )
        if process.returncode == 0 and process.stdout:
            try:
                return json.loads(process.stdout)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON for {url}")
                return None
        logger.warning(f"streamlink --json for {url} failed. stderr: {process.stderr[:100]}")
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout fetching JSON metadata for {url}")
        return None
    except FileNotFoundError:
        logger.critical("streamlink command not found during JSON metadata fetch.")
        raise FileNotFoundError("streamlink command not found during JSON metadata fetch.")
    except Exception as e:
        logger.exception(f"Error fetching JSON metadata for {url}")
        return None

def extract_category_keywords(metadata_json, platform, url_type='unknown'):
    """Extracts category/keywords from streamlink's JSON metadata based on platform."""
    if not metadata_json or 'metadata' not in metadata_json:
        return "N/A"
    meta = metadata_json.get('metadata', {})
    title = meta.get('title', "")

    # Helper to clean titles
    def clean_common_prefixes(text):
        return re.sub(r"^\(?(LIVE|EN DIRECT|ОНЛАЙН|생방송|ライブ)[\]:]*\s*", "", text, flags=re.IGNORECASE).strip()

    # --- Platform Specific Logic ---
    if platform == 'Twitch':
        return meta.get('game') or (title.split(' ')[0] if title else "N/A")
    
    elif platform == 'YouTube':
        clean_title = clean_common_prefixes(title)
        words = clean_title.split()
        if len(words) > 0 and len(words[0]) <= 2 and len(words) > 1 and words[0].upper() not in ["A", "AN", "BE", "IN", "IS", "IT", "OF", "ON", "OR", "SO", "TO", "EL", "LA", "DE"]:
             return " ".join(words[1:4]) if len(words) > 1 else clean_title
        return " ".join(words[:3]) if words else "N/A"

    elif platform == 'Kick':
        # Kick often has category in title or a specific field if plugin supports
        # Assuming title is primary for now if no dedicated field found in your tests
        return title.split(':')[0].strip() if ':' in title else (title.split(' ')[0] if title else "N/A")

    elif platform == 'TikTok' or platform == 'Douyin' or platform == 'Bigo Live':
        # Title is primary; may contain hints.
        return clean_common_prefixes(title) if title else "N/A" # Return more of the title

    elif platform == 'BiliBili':
        category = meta.get('game_name', meta.get('category'))
        if category: return category
        return clean_common_prefixes(title).split(' - ')[0] if ' - ' in title else (title.split(' ')[0] if title else "N/A")

    elif platform == 'Vimeo' or platform == 'Dailymotion':
        # Title usually contains event/stream description
        return clean_common_prefixes(title) if title else "N/A"

    elif platform == 'PlutoTV':
        return meta.get('program_title') or meta.get('title') or "Live TV" # Current show

    elif platform == 'Huya':
        return meta.get('game_name', meta.get('category')) or (title.split(' ')[0] if title else "N/A")

    elif platform in ['BBC iPlayer', 'RaiPlay', 'Atresplayer', 'RTVE Play', 
                      'ARD Mediathek', 'ZDF Mediathek', 'Mitele', 'AbemaTV']:
        # For broadcasters, the program title is the category
        return meta.get('program_title', meta.get('title')) or "Live Broadcast"

    elif platform == 'Adult Swim':
        return meta.get('title') or "Live Stream" # Title is often the show

    elif platform == 'Bloomberg':
        return meta.get('title') or "Live News" # Title is the show/feed

    # --- Generic Fallback ---
    if title:
        clean_title = clean_common_prefixes(title)
        return " ".join(clean_title.split()[:3]) # First 3 words of cleaned title as a generic category
    return "N/A"

def fetch_live_streams(all_configured_streams):
    """
    Fetches the list of currently live streams with enhanced metadata.
    Returns a list of dictionaries:
    [{'url': '...', 'username': '...', 'platform': '...', 'category_keywords': '...', 'is_live': True}, ...]
    """
    if not all_configured_streams:
        logger.info("No configured streams to check.")
        return []

    logger.info("Checking stream liveness, please wait...")
    live_stream_candidates = [] # URLs that are live

    # Phase 1: Quick Liveness Check
    with ThreadPoolExecutor(max_workers=config.get_max_workers_liveness()) as executor:
        future_to_url = {executor.submit(is_stream_live_for_check, url): url for url in all_configured_streams}
        for future in as_completed(future_to_url):
            is_live, url = future.result() # is_stream_live_for_check must return (bool, url)
            if is_live:
                live_stream_candidates.append(url)
    
    if not live_stream_candidates:
        logger.info("No streams appear to be live based on initial check.")
        return []

    logger.info(f"Found {len(live_stream_candidates)} potentially live stream(s). Fetching details...")
    
    # Phase 2: Fetch detailed metadata for live candidates
    detailed_live_streams = []
    with ThreadPoolExecutor(max_workers=config.get_max_workers_metadata()) as executor:
        future_to_meta_task = {}
        for url in live_stream_candidates:
            parsed_initial_info = parse_url_metadata(url)
            future = executor.submit(get_stream_metadata_json, url)
            future_to_meta_task[future] = {
                'url': url,
                'initial_platform': parsed_initial_info['platform'],
                'initial_username': parsed_initial_info['username'],
                'url_type': parsed_initial_info.get('type', 'unknown')
            }

        for future in as_completed(future_to_meta_task):
            task_info = future_to_meta_task[future]
            url, initial_platform, initial_username, url_type = \
                task_info['url'], task_info['initial_platform'], \
                task_info['initial_username'], task_info['url_type']
            
            final_username = initial_username
            final_platform = initial_platform # Usually doesn't change from initial parse
            category = "N/A (no details)"

            try:
                metadata_json = future.result()
                if metadata_json and 'metadata' in metadata_json:
                    meta = metadata_json['metadata']
                    
                    # Refine username based on platform-specific metadata fields
                    # This uses the detailed info you provided.
                    author_field = None
                    if final_platform == 'Twitch': author_field = meta.get('user_name') # More accurate than login sometimes
                    elif final_platform == 'YouTube': author_field = meta.get('author', meta.get('channel', meta.get('uploader')))
                    elif final_platform == 'Kick': author_field = meta.get('user', {}).get('username') # Example, check Kick JSON
                    elif final_platform in ['TikTok', 'Douyin', 'BiliBili', 'Huya', 'Bigo Live']: author_field = meta.get('author', meta.get('nick'))
                    elif final_platform in ['Vimeo', 'Dailymotion']: author_field = meta.get('uploader', meta.get('channel', meta.get('author')))
                    # For broadcasters, initial_username (channel_id/slug) is often refined by a 'channel_title' or similar
                    elif final_platform == 'PlutoTV': author_field = meta.get('channel_name', meta.get('station_id'))
                    elif final_platform == 'BBC iPlayer': author_field = meta.get('channel_title', meta.get('service_name'))
                    elif final_platform == 'RaiPlay': author_field = meta.get('channel', meta.get('name'))
                    elif final_platform == 'Atresplayer': author_field = meta.get('channel_name')
                    elif final_platform == 'RTVE Play': author_field = meta.get('channel', meta.get('id')) # or title if it's the channel itself
                    elif final_platform == 'ARD Mediathek': author_field = meta.get('channelTitle', meta.get('station'))
                    elif final_platform == 'ZDF Mediathek': author_field = meta.get('channel', meta.get('stationName'))
                    elif final_platform == 'Mitele': author_field = meta.get('channel_name')
                    elif final_platform == 'AbemaTV': author_field = meta.get('channelName')
                    elif final_platform == 'Adult Swim': author_field = meta.get('title') # Title often is the "channel"
                    elif final_platform == 'Bloomberg': author_field = meta.get('title') # Title often is the "feed"

                    if author_field:
                        final_username = author_field
                    
                    category = extract_category_keywords(metadata_json, final_platform, url_type)
                else:
                    category = "N/A (details unavailable)"
                
                detailed_live_streams.append({
                    'url': url, 'username': final_username, 'platform': final_platform,
                    'category_keywords': category, 'is_live': True
                })
            except FileNotFoundError as e:
                 logger.critical(f"streamlink command not found during metadata fetch for {url}")
                 raise  # Propagate critical streamlink error
            except Exception as e:
                logger.exception(f"Error fetching metadata for {url}")
                # Fallback: add with basic info if metadata fetch failed but was initially live
                detailed_live_streams.append({
                    'url': url, 'username': initial_username, 'platform': initial_platform,
                    'category_keywords': f"N/A (err: {str(e)[:20]})", 'is_live': True
                })
    
    # Sort the detailed_live_streams list to match the order of live_stream_candidates
    # if original order from all_configured_streams is important for display.
    # For now, the order from as_completed will be used.
    # To maintain original order:
    ordered_final_streams = []
    url_to_details_map = {s['url']: s for s in detailed_live_streams} # Build map once
    for original_url in all_configured_streams:
        if original_url in url_to_details_map:
            ordered_final_streams.append(url_to_details_map[original_url])
            
    return ordered_final_streams