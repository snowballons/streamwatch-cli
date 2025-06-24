# stream_manager_cli/stream_utils.py (NEW FILE)
import re

# Helper to create a consistent result structure
def _result(platform, username, url_type="unknown"):
    return {'platform': platform, 'username': username, 'type': url_type}

def parse_url_metadata(url):
    """
    Parses a stream URL to extract platform, a preliminary username/ID, and URL type.
    """
    # Order matters: more specific patterns first.

    # --- Tier 1: Top User-Facing Platforms ---
    # Twitch
    m = re.match(r"https?://(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('Twitch', m.group(1), 'channel')

    # YouTube (Channel handles, /channel/, /c/, /user/, live video, regular video)
    m = re.match(r"https?://(?:www\.)?youtube\.com/(?:@([a-zA-Z0-9_.-]+)(?!/.*)|channel/([a-zA-Z0-9_-]+)|c/([a-zA-Z0-9_.-]+)|user/([a-zA-Z0-9_.-]+))", url, re.IGNORECASE)
    if m: return _result('YouTube', m.group(1) or m.group(2) or m.group(3) or m.group(4), 'channel')
    m = re.match(r"https?://(?:www\.)?youtube\.com/(?:live/([a-zA-Z0-9_-]+)|watch\?v=([a-zA-Z0-9_-]+))", url, re.IGNORECASE)
    if m: return _result('YouTube', m.group(1) or m.group(2), 'video') # Username is video_id initially

    # Kick
    m = re.match(r"https?://(?:www\.)?kick\.com/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('Kick', m.group(1), 'channel')

    # TikTok
    m = re.match(r"https?://(?:www\.)?tiktok\.com/@([a-zA-Z0-9_.-]+)(?:/live)?", url, re.IGNORECASE)
    if m: return _result('TikTok', m.group(1), 'channel_live')
    m = re.match(r"https?://(?:www\.)?tiktok\.com/live\?creator=([a-zA-Z0-9_.-]+)", url, re.IGNORECASE) # Less common input
    if m: return _result('TikTok', m.group(1), 'channel_live_param')


    # --- Tier 2: Major International & Niche ---
    # Bilibili
    m = re.match(r"https?://live\.bilibili\.com/([0-9]+)", url, re.IGNORECASE)
    if m: return _result('BiliBili', m.group(1), 'live_room_id')
    m = re.match(r"https?://(?:www\.)?bilibili\.com/video/(BV[a-zA-Z0-9]+)", url, re.IGNORECASE) # VODs, but SL might use for some live events
    if m: return _result('BiliBili', m.group(1), 'video_id') # User is video_id initially

    # Vimeo
    m = re.match(r"https?://vimeo\.com/event/([0-9]+)", url, re.IGNORECASE)
    if m: return _result('Vimeo', f"event_{m.group(1)}", 'event')
    m = re.match(r"https?://vimeo\.com/([a-zA-Z0-9_-]+)(?:/live)?", url, re.IGNORECASE) # User or custom URL
    if m: return _result('Vimeo', m.group(1), 'user_or_custom_url')

    # Dailymotion
    m = re.match(r"https?://(?:www\.)?dailymotion\.com/video/([a-zA-Z0-9]+)", url, re.IGNORECASE)
    if m: return _result('Dailymotion', m.group(1), 'video_id') # video_id, channel name from metadata
    m = re.match(r"https?://(?:www\.)?dailymotion\.com/([a-zA-Z0-9_.-]+)", url, re.IGNORECASE) # User profile
    if m: return _result('Dailymotion', m.group(1), 'channel')

    # Pluto TV
    m = re.match(r"https?://pluto\.tv/live-tv/([a-zA-Z0-9_-]+)", url, re.IGNORECASE)
    if m: return _result('PlutoTV', m.group(1), 'channel_slug') # Channel name from metadata

    # Adult Swim
    m = re.match(r"https?://(?:www\.)?adultswim\.com/streams(?:/([a-zA-Z0-9_-]+))?", url, re.IGNORECASE)
    if m: return _result('Adult Swim', m.group(1) or "live", 'stream_slug') # Show name from metadata

    # Bloomberg
    m = re.match(r"https?://(?:www\.)?bloomberg\.com/live(?:/([a-zA-Z0-9_-]+))?", url, re.IGNORECASE)
    if m: return _result('Bloomberg', m.group(1) or "main", 'feed_slug') # Show/feed name from metadata


    # --- Tier 3: Chinese Platforms ---
    # Douyin
    m = re.match(r"https?://live\.douyin\.com/([0-9]+)", url, re.IGNORECASE)
    if m: return _result('Douyin', m.group(1), 'live_room_id')
    # m = re.match(r"https?://v\.douyin\.com/([a-zA-Z0-9]+)", url, re.IGNORECASE) # Shortlinks, harder to parse directly for type
    # if m: return _result('Douyin', m.group(1), 'shortlink')

    # Huya
    m = re.match(r"https?://(?:www\.)?huya\.com/([a-zA-Z0-9_-]+)", url, re.IGNORECASE) # Can be room ID or username
    if m: return _result('Huya', m.group(1), 'room_or_user')


    # --- Tier 4: European Public Broadcasters & Regional ---
    # BBC iPlayer (UK)
    m = re.match(r"https?://(?:www\.)?bbc\.co\.uk/iplayer/live/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('BBC iPlayer', m.group(1), 'channel_id') # e.g., bbc_one

    # RaiPlay (Italy)
    m = re.match(r"https?://(?:www\.)?raiplay\.it/dirette/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('RaiPlay', m.group(1), 'channel_id') # e.g., rai1

    # Atresplayer (Spain)
    m = re.match(r"https?://(?:www\.)?atresplayer\.com/(?:directos|player)/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('Atresplayer', m.group(1), 'channel_slug') # e.g., antena3

    # RTVE Play (Spain)
    m = re.match(r"https?://(?:www\.)?rtve\.es/play/(?:videos/)?directo(?:/([a-zA-Z0-9_-]+))?", url, re.IGNORECASE)
    if m: return _result('RTVE Play', m.group(1) or "general", 'channel_slug') # e.g., la1

    # ARD Mediathek (Germany)
    m = re.match(r"https?://(?:www\.)?ardmediathek\.de/(?:live|player)/([a-zA-Z0-9_-]+)(?:/([a-zA-Z0-9_-]+))?", url, re.IGNORECASE)
    # ARD URLs can be complex, e.g., ardmediathek.de/player/Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhZ2Vzc2NoYXUvYmI4YWYxYTAtZA
    # For live, it's often /live/CHANNEL_ID like /live/daserste
    # The regex below is a simplification.
    if m:
        channel_part = m.group(1)
        if channel_part.lower() == "live" and m.group(2): # ardmediathek.de/live/daserste
            return _result('ARD Mediathek', m.group(2), 'channel_id')
        return _result('ARD Mediathek', channel_part, 'player_id_or_channel') # Fallback if not /live/ format

    # ZDF Mediathek (Germany)
    m = re.match(r"https?://(?:www\.)?zdf\.de/live-tv(?:/([a-zA-Z0-9_-]+))?", url, re.IGNORECASE)
    # e.g., zdf.de/live-tv or zdf.de/live-tv/zdfneo
    if m: return _result('ZDF Mediathek', m.group(1) or "zdf", 'channel_id')

    # Mitele (Spain)
    m = re.match(r"https?://(?:www\.)?mitele\.es/directo/([a-zA-Z0-9_]+)", url, re.IGNORECASE)
    if m: return _result('Mitele', m.group(1), 'channel_slug') # e.g., telecinco

    # AbemaTV (Japan)
    m = re.match(r"https?://abema\.tv/(?:now-on-air|channels)/([a-zA-Z0-9_-]+)", url, re.IGNORECASE)
    if m: return _result('AbemaTV', m.group(1), 'channel_id')

    # Bigo Live
    m = re.match(r"https?://(?:www\.)?bigo\.tv/([a-zA-Z0-9_]+)", url, re.IGNORECASE) # Can be user ID or vanity name
    if m: return _result('Bigo Live', m.group(1), 'user_id_or_vanity')


    # --- Fallback for unknown URLs ---
    try:
        domain_match = re.match(r"https?://(?:www\.)?([a-zA-Z0-9.-]+)", url, re.IGNORECASE)
        domain_parts = domain_match.group(1).split('.') if domain_match else ["Unknown"]
        platform_name = domain_parts[-2] if len(domain_parts) >=2 else domain_parts[0] # e.g. 'google' from 'drive.google.com'
        platform_name = platform_name.capitalize()

        path_parts = [part for part in url.split('/') if part and '.' not in part and part.lower() not in ('http:','https:','www')]
        username_guess = path_parts[-1] if path_parts else "stream"
        
        # Avoid using common path segments like 'live', 'channel', 'streams', 'videos', 'directo', 'directos', 'player' as username
        if username_guess.lower() in ['live', 'channel', 'streams', 'videos', 'directo', 'directos', 'player'] and len(path_parts) > 1:
            username_guess = path_parts[-2] if path_parts[-2].lower() not in ['http:','https:','www'] else username_guess
        
        return _result(platform_name, username_guess, 'generic_fallback')
    except Exception:
        return _result('Unknown', 'unknown_stream', 'parse_error')