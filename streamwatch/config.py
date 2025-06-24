import os
import configparser
from pathlib import Path
import logging # Import logging

# --- Core Application Details ---
APP_NAME = "streamwatch" # Renamed from stream-manager-cli

# Get a logger for this module
logger = logging.getLogger(APP_NAME + ".config")

# --- Default Configuration Values ---
DEFAULT_CONFIG = {
    'Streamlink': {
        'quality': 'best',
        'timeout_liveness': '10',  # seconds for initial liveness check
        'timeout_metadata': '15', # seconds for fetching JSON metadata
        'max_workers_liveness': '4',
        'max_workers_metadata': '2', # Often fewer streams need metadata fetch
        'twitch_disable_ads': 'true'
    },
    'Interface': {
        # Color settings could go here later
        # 'color_live': 'green',
        # 'color_username': 'cyan',
    },
    'Misc': {
        'donation_link': 'https://buymeacoffee.com/snowballons', # Your actual link
        'first_run_completed': 'false', # For First-Time UX
        'last_played_url': '' # Add this
    }
}

# --- Paths ---
def get_user_config_dir():
    """Gets the platform-specific user configuration directory for the app."""
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
    return Path.home() / f".{APP_NAME}" # Fallback

USER_CONFIG_DIR = get_user_config_dir()
CONFIG_FILE_PATH = USER_CONFIG_DIR / "config.ini"
STREAMS_FILE_PATH = USER_CONFIG_DIR / "streams.json" # Keep this as is

# --- Config Loading and Management ---
config_parser = configparser.ConfigParser()

def create_default_config_file():
    """Creates the config.ini file with default values if it doesn't exist."""
    if not CONFIG_FILE_PATH.exists():
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        temp_parser = configparser.ConfigParser()
        for section, options in DEFAULT_CONFIG.items():
            temp_parser[section] = {}
            for key, value in options.items():
                temp_parser[section][key] = str(value)
        
        try:
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as configfile:
                temp_parser.write(configfile)
            logger.info(f"Created default configuration file at {CONFIG_FILE_PATH}")
            return True # Indicates file was created
        except IOError as e:
            logger.error(f"Could not write default config file: {e}", exc_info=True)
            return False
    return False # File already existed

def load_config():
    """Loads configuration from file, falling back to defaults."""
    global config_parser # Use the module-level parser
    
    # Ensure USER_CONFIG_DIR exists before trying to read/write config
    try:
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create config directory {USER_CONFIG_DIR}: {e}", exc_info=True)
        # In this critical case, we might have to rely on hardcoded defaults entirely
        # or exit. For now, it will try to proceed but likely fail to save.

    create_default_config_file() # Create if it doesn't exist

    try:
        if CONFIG_FILE_PATH.exists():
            config_parser.read(CONFIG_FILE_PATH, encoding='utf-8')
        else: # Should have been created, but as a fallback, load defaults into parser
            for section, options in DEFAULT_CONFIG.items():
                if section not in config_parser: config_parser.add_section(section)
                for key, value in options.items():
                    config_parser.set(section, key, str(value))

    except configparser.Error as e:
        logger.error(f"Could not parse config file {CONFIG_FILE_PATH}: {e}. Using defaults.", exc_info=True)
        # Re-initialize parser with defaults if parsing failed
        config_parser = configparser.ConfigParser() # Reset
        for section, options in DEFAULT_CONFIG.items():
            if section not in config_parser: config_parser.add_section(section)
            for key, value in options.items():
                config_parser.set(section, key, str(value))


# --- Accessor Functions for Configuration Values ---
# These functions will get values from the loaded config_parser,
# or return a hardcoded default if the section/key is missing (robustness).

def get_streamlink_quality():
    return config_parser.get('Streamlink', 'quality', fallback=DEFAULT_CONFIG['Streamlink']['quality'])

def get_streamlink_timeout_liveness():
    return config_parser.getint('Streamlink', 'timeout_liveness', fallback=int(DEFAULT_CONFIG['Streamlink']['timeout_liveness']))

def get_streamlink_timeout_metadata():
    return config_parser.getint('Streamlink', 'timeout_metadata', fallback=int(DEFAULT_CONFIG['Streamlink']['timeout_metadata']))

def get_max_workers_liveness():
    return config_parser.getint('Streamlink', 'max_workers_liveness', fallback=int(DEFAULT_CONFIG['Streamlink']['max_workers_liveness']))

def get_max_workers_metadata():
    return config_parser.getint('Streamlink', 'max_workers_metadata', fallback=int(DEFAULT_CONFIG['Streamlink']['max_workers_metadata']))

def get_twitch_disable_ads():
    return config_parser.getboolean('Streamlink', 'twitch_disable_ads', fallback=DEFAULT_CONFIG['Streamlink']['twitch_disable_ads'].lower() == 'true')

def get_donation_link():
    return config_parser.get('Misc', 'donation_link', fallback=DEFAULT_CONFIG['Misc']['donation_link'])

def is_first_run_completed():
    return config_parser.getboolean('Misc', 'first_run_completed', fallback=DEFAULT_CONFIG['Misc']['first_run_completed'].lower() == 'true')

def mark_first_run_completed():
    """Marks that the first run experience has been completed."""
    if 'Misc' not in config_parser:
        config_parser.add_section('Misc')
    config_parser.set('Misc', 'first_run_completed', 'true')
    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
        logger.info("Marked first run as completed in config file.")
    except IOError as e:
        logger.error(f"Could not update config file for first_run: {e}", exc_info=True)

def get_last_played_url():
    return config_parser.get('Misc', 'last_played_url', fallback='')

def set_last_played_url(url):
    if 'Misc' not in config_parser:
        config_parser.add_section('Misc')
    config_parser.set('Misc', 'last_played_url', url if url else '') # Store empty if None
    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
        logger = logging.getLogger(APP_NAME + ".config") # Get logger here
        logger.debug(f"Saved last_played_url: {url}")
    except IOError as e:
        logger = logging.getLogger(APP_NAME + ".config")
        logger.error(f"Could not update config file for last_played_url: {e}")

# --- Load config when module is imported ---
load_config()

# --- OLD Constants (to be removed or made to use the getters above) ---
# STREAMLINK_TIMEOUT = 10 (replace with get_streamlink_timeout_liveness/metadata)
# MAX_WORKERS = 4 (replace with get_max_workers_liveness/metadata)
# STREAM_QUALITY = "best" (replace with get_streamlink_quality)
# TWITCH_DISABLE_ADS = True (replace with get_twitch_disable_ads)
# DONATION_LINK = "..." (replace with get_donation_link)