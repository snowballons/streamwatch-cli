# Stream Manager CLI

[![PyPI version](https://img.shields.io/pypi/v/stream-manager-cli.svg)](https://pypi.org/project/stream-manager-cli/0.2.0/) <!-- Replace with actual PyPI badge once live -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- Add other badges if you set them up, e.g., build status, Python versions -->

![Stream Manager CLI Logo](assets/images/logoign.png)

A simple, lightweight command-line tool to manage your favorite live streams, check their status efficiently, and launch them directly in your media player **without needing a heavy web browser.**

![Stream Manager CLI guide](assets/gifs-videos/stream-manager-cli.gif)

Tired of opening multiple browser tabs just to check if your favorite streamers are live? Stream Manager CLI provides a clean terminal interface to see who's online and play their streams instantly.

## Features

*   **Live Status Checks:** Quickly see which of your favorite streams are currently live using concurrent checks for speed.
*   **Direct Playback:** Launch live streams directly in your media player (via `streamlink`) with your chosen quality.
*   **Browser-Free:** Saves system resources (CPU, RAM) by avoiding heavy web browsers for checking and viewing streams.
*   **Interactive Menu:** Simple text-based menu for easy navigation and stream selection.
*   **Stream Management:**
    *   Add new stream URLs directly within the tool.
    *   Add multiple URLs at once (comma-separated).
    *   Remove unwanted streams easily via a numbered list.
*   **Persistent Storage:** Your stream list is saved automatically in a user configuration directory.
*   **Configurable Quality:** Set your preferred stream quality (e.g., "best", "720p") for playback.
*   **Manual Refresh:** Update the live stream list on demand without restarting the tool.

## Why Use Stream Manager CLI?

*   **Save System Resources:** The biggest advantage! Checking and watching streams without a browser significantly reduces CPU and RAM usage, especially on less powerful machines.
*   **Simplicity & Speed:** A single, fast interface to check all your favorites and launch streams instantly.
*   **Focus:** Avoid the distractions of browser notifications, ads (Twitch ad blocking is attempted via streamlink), and extra tabs.
*   **Centralized List:** Keep all your favorite stream URLs organized in one place, managed directly through the tool.

## Prerequisites

Before using Stream Manager CLI, ensure you have the following installed:

1.  **Python:** Version 3.7 or higher is required. You can check your version with `python --version` or `python3 --version`. Download Python from [python.org](https://www.python.org/) if needed.

2.  **Streamlink:** This is the core engine that finds and extracts stream data. Stream Manager CLI uses it to check live status and launch streams. If you install Stream Manager CLI using `pip` (recommended), `streamlink` will be installed automatically as a dependency. Learn more at [streamlink.github.io](https://streamlink.github.io/).

3.  **MPV Media Player:** Streamlink needs a media player to display the video. While it supports others like VLC, **MPV is highly recommended** for the simplest out-of-the-box experience with this tool. Using MPV avoids potential configuration issues where `streamlink` might not find or correctly interact with other players.
    *   Download MPV from [mpv.io](https://mpv.io/). Ensure the `mpv` command is available in your system's PATH (usually handled by the installer).

## Installation

The recommended way to install Stream Manager CLI is using `pip`:

```bash
pip install stream-manager-cli
```
This command will download the tool from the Python Package Index (PyPI) and automatically install its dependency (streamlink).
<details>
<summary>Alternative: Installation from Source (for development or manual setup)</summary>
Follow these steps if you want to run the tool directly from the source code. This requires you to have git installed.
(Make sure you have met all the requirements listed in the Prerequisites section first!)
1. Clone the Repository
Open your terminal or command prompt and navigate to the directory where you want to store the project. Then, run the following command to download the code:

```bash
git clone https://github.com/snowballons/stream-manager-cli.git
```
Now, change into the newly created project directory:

```bash
cd stream-manager-cli
```

2. Create and Activate a Virtual Environment (Highly Recommended)
Create: python -m venv venv (Use python3 if needed on Linux/macOS)
Activate:
* Linux / macOS:
```bash
  source venv/bin/activate
```
* Windows:
```bash
  venv\Scripts\activate
```
3. Install Dependencies
With the virtual environment activated, install the necessary libraries:

```bash
pip install -r requirements.txt
```
4. Running the Tool (from Source)
Make sure you are inside the root stream-manager-cli directory with the virtual environment activated. Run using:

```bash
python -m stream_manager_cli.main
```
</details>

## Usage
1. Run the tool: Once installed via pip, simply open your terminal and type:

```bash
stream-manager
```

2. First Run: The tool will automatically create a configuration directory and an empty stream list file (streams.json). It will prompt you to add your first stream URLs using the [A] option.
3. Interactive Menu: You will be presented with a menu:

 **[number]** (If live streams are available): Enter the number corresponding to a live stream to start playing it immediately using MPV (or your default player configured for streamlink).
 
**[L]**: List all the stream URLs currently saved in your configuration.

**[A]**: Add one or more new stream URLs. You'll be prompted to enter URLs, separated by commas if adding multiple. The tool checks for basic http:// or https:// format and avoids duplicates.

**[R]**: Remove stream URLs. You'll be shown a numbered list of all your configured streams, and you can enter the numbers (space or comma-separated) of the streams you wish to remove.

**[F]**: Force a refresh of the live stream status list.

**[Q]**: Quit the application.

## Configuration File

Stream Manager CLI stores your list of stream URLs in a streams.json file located in a platform-specific user configuration directory:

Linux/macOS: Typically ~/.config/stream-manager-cli/streams.json (or $XDG_CONFIG_HOME/stream-manager-cli/streams.json if XDG_CONFIG_HOME is set).
Windows: Typically %APPDATA%\stream-manager-cli\streams.json (e.g., C:\Users\YourUser\AppData\Roaming\stream-manager-cli\streams.json).

You generally don't need to edit this file manually, as adding and removing streams is handled through the [A] and [R] menu options.
Other settings (like stream quality, timeouts) are currently defined within the package's config.py file. Modifying these requires editing the source code if installed manually, or would require forking/reinstalling if installed via pip.

## Contributing
Contributions are welcome! If you find a bug or have an idea for a new feature, please:
1. Check the existing Issues to see if it has already been reported or discussed.
2. If not, open a new issue describing the bug or feature request.
3. If you'd like to contribute code, please fork the repository and submit a pull request.
## License
This project is licensed under the MIT License. See the LICENSE file for details.
