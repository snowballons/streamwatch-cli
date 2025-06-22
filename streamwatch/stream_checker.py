import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from . import config

def is_stream_live_for_check(url):
    """
    Checks if a given stream URL is currently live using streamlink.
    Returns a tuple: (bool_is_live, url)
    """
    command = ["streamlink"]
    if config.TWITCH_DISABLE_ADS:
        command.append("--twitch-disable-ads")
    command.append(url)

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=config.STREAMLINK_TIMEOUT,
            check=False
        )
        if process.returncode == 0 and "Available streams:" in process.stdout:
            return True, url

        stderr_lower = process.stderr.lower()
        stdout_lower = process.stdout.lower()
        if "no playable streams found" in stderr_lower or \
           "error: no streams found on" in stderr_lower or \
           "this stream is offline" in stdout_lower or \
           process.returncode != 0:
            return False, url
        return False, url # Default to not live for ambiguous cases
    except subprocess.TimeoutExpired:
        return False, url
    except FileNotFoundError:
        # Re-raise specifically to be caught higher up and halt execution if needed
        raise FileNotFoundError("streamlink command not found during check.")
    except Exception: # Catch any other exception during the check for a single stream
        # Optionally log the error here if needed: print(f"Error checking {url}: {e}", file=sys.stderr)
        return False, url

def fetch_live_streams(all_configured_streams):
    """
    Fetches the list of currently live streams from the configured list.
    Returns a list of live URLs.
    """
    live_streams_found = []
    if not all_configured_streams:
        return []

    print("Checking stream statuses, please wait...")
    # Using ThreadPoolExecutor to check streams concurrently
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        future_to_url = {executor.submit(is_stream_live_for_check, url): url for url in all_configured_streams}

        results_map = {}
        for future in as_completed(future_to_url):
            original_url = future_to_url[future]
            try:
                is_live, _ = future.result()
                results_map[original_url] = is_live
            except FileNotFoundError as e: # Propagated from is_stream_live_for_check
                 raise FileNotFoundError(f"CRITICAL: {e}") # Propagate up to halt the program
            except Exception as exc:
                print(f"\nError processing {original_url} during fetch: {exc}", file=sys.stderr)
                results_map[original_url] = False

    # Maintain original order from streams.txt for live streams if desired
    for url in all_configured_streams:
        if results_map.get(url, False):
            live_streams_found.append(url)

    return live_streams_found