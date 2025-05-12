import os
from pathlib import Path

# --- Core Configuration ---
APP_NAME = "stream-manager-cli"

# --- Streamlink Configuration ---
STREAMLINK_TIMEOUT = 10       # Seconds to wait for streamlink liveness check
MAX_WORKERS = 4               # Max concurrent streamlink processes for liveness check
STREAM_QUALITY = "best"       # Quality to pass to streamlink (e.g., "best", "720p")
TWITCH_DISABLE_ADS = True    # Attempt to disable Twitch ads (requires specific streamlink version/plugins)

# --- Storage Configuration ---
def get_config_dir():
    """Gets the platform-specific configuration directory."""
    if os.name == 'nt': # Windows
        app_data = os.getenv('APPDATA')
        if app_data:
            return Path(app_data) / APP_NAME
    else: # Linux, macOS, etc.
        xdg_config_home = os.getenv('XDG_CONFIG_HOME')
        if xdg_config_home:
            return Path(xdg_config_home) / APP_NAME
        else:
            return Path.home() / '.config' / APP_NAME
    # Fallback if unsure
    return Path.home() / f".{APP_NAME}"

CONFIG_DIR = get_config_dir()
STREAMS_FILE_PATH = CONFIG_DIR / "streams.json" # Store streams as JSON

# Ensure the config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)