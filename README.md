# StreamWatch: Your Lightweight CLI Live Stream Companion

[![PyPI version](https://img.shields.io/pypi/v/streamwatch.svg)](https://pypi.org/project/streamwatch/)
[![Python Versions](https://img.shields.io/pypi/pyversions/streamwatch.svg)](https://pypi.org/project/streamwatch/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/snowballons/streamwatch-cli.svg?style=social)](https://github.com/snowballons/streamwatch-cli)

<p align="center">
  <img src="assets/Images/logoign.png" alt="StreamWatch Logo" width="150"/>
</p>

**StreamWatch** is a fast, efficient, and distraction-free command-line tool for managing and watching your favorite live streams—no browser required!

<p align="center">
  <img src="assets/Images/streamwatch-cli.gif" alt="StreamWatch CLI in action" width="700"/>
  <br/>
</p>

---

## Table of Contents

- [Why StreamWatch?](#why-streamwatch)
- [Key Features](#key-features)
- [Supported Platforms](#supported-platforms)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Why StreamWatch?

- 🚀 **Lightweight & Fast:** No more resource-hungry browsers.
- 🎯 **Focus-Friendly:** No ads, popups, or web clutter.
- 💡 **Efficient Workflow:** Check all your favorites and launch streams from a single interface.
- ⚙️ **Customizable:** Tweak quality, performance, and more.
- 📺 **Broad Platform Support:** Works with any site supported by Streamlink.
- 🖥️ **Cross-Platform:** Windows, macOS, and Linux.

---

## Key Features

- **Live Status Display:** See who's live, with username, platform, and category/game.
- **Interactive Navigation:** Use arrow keys, numbers, or search to select streams.
- **Direct Playback:** Launches streams in your media player (MPV recommended) via Streamlink.
- **Playback Controls:** Stop, next/previous, change quality, return to menu, or donate—all from the terminal.
- **Stream Management:** Add, remove, and list your favorite streams.
- **Persistent Configuration:** User-editable `streams.json` and `config.ini`.
- **Automatic Reconnection:** Tries to reconnect if a stream drops.
- **Quick Access:** Instantly replay the last stream you watched.
- **Colorful Interface:** Uses `rich` for a beautiful terminal experience.
- **Detailed Logging:** For troubleshooting and support.

---

## Supported Platforms

StreamWatch uses [Streamlink](https://streamlink.github.io/) under the hood, so it supports any platform Streamlink does. Enhanced display features are available for:

- YouTube, Twitch, Kick, TikTok, BiliBili, Douyin, Huya, Vimeo, Dailymotion, PlutoTV
- Major European broadcasters (BBC iPlayer, ARD/ZDF Mediathek, RaiPlay, RTVE Play, Atresplayer, Mitele)
- AbemaTV, Adult Swim, Bloomberg, Bigo Live, and more!

If your platform isn't listed, StreamWatch will still try to display what it can, and playback will work if Streamlink supports the URL.

---

## Prerequisites

- **Python 3.7+** ([Download](https://www.python.org/))
- **Streamlink** (installed automatically with pip)
- **MPV Media Player** ([Download](https://mpv.io/)) — recommended for best results

---

## Installation

### Using pip (Recommended)

```bash
pip install streamwatch
```

This will install StreamWatch and all dependencies, including Streamlink.

### From Source (for Development)

```bash
git clone https://github.com/snowballons/streamwatch-cli.git
cd streamwatch-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run StreamWatch from source:

```bash
streamwatch
```

---

## Getting Started

### First Run

- On first launch, StreamWatch creates a config directory, a default `config.ini`, and an empty `streams.json`.
- You'll see a welcome message with instructions.

<p align="center">
<img src="assets/Images/first-run.png" alt="StreamWatch First Run Experience" width="600"/>
</p>

### Adding Streams

- From the main menu, press **A** (Add).
- Enter one or more stream URLs (comma-separated for multiple).
  - Example:  
    ```
    https://twitch.tv/streamer1, https://youtube.com/@channel2, https://kick.com/user3
    ```
- Your streams are saved to `streams.json`.

---

## Usage Guide

### Main Menu Navigation

- **[Enter]**: Select a live stream interactively.
- **[Number]**: Play a stream by its number.
- **[L]**: List all configured streams.
- **[A]**: Add new streams.
- **[R]**: Remove streams.
- **[P]**: Play last watched stream (if available).
- **[F]**: Refresh live stream list.
- **[Q]**: Quit StreamWatch.

### Playing a Stream

- Select a stream and StreamWatch launches it in your media player via Streamlink.

### Playback Controls

- **[S]**: Stop stream
- **[N]**: Next live stream
- **[P]**: Previous live stream
- **[C]**: Change quality
- **[M]**: Main menu
- **[D]**: Donate to developer
- **[Q]**: Quit StreamWatch

If the stream ends or you close the player, StreamWatch returns you to the menu. If a stream drops, it will try to reconnect for about 30 seconds.

---

## Configuration

StreamWatch uses two main files:

### Stream List (`streams.json`)

- Stores your stream URLs.
- **Location:**
  - Linux/macOS: `~/.config/streamwatch/streams.json`
  - Windows: `%APPDATA%\\StreamWatch\\streams.json`
- Manage via the [A] (Add) and [R] (Remove) options.

### Settings (`config.ini`)

- Created on first run, editable with any text editor.
- **Location:** Same as `streams.json`.

Example:

```ini
[Streamlink]
quality = best
timeout_liveness = 10
timeout_metadata = 15
max_workers_liveness = 4
max_workers_metadata = 2
twitch_disable_ads = true

[Misc]
donation_link = https://buymeacoffee.com/snowballons
first_run_completed = true
last_played_url =
```

---

## Logging

- Log file for troubleshooting:  
  - Linux/macOS: `~/.config/streamwatch/logs/streamwatch.log`
  - Windows: `%APPDATA%\\StreamWatch\\logs\\streamwatch.log`
- Includes INFO, WARNING, ERROR, and DEBUG messages.
- Log files are rotated automatically.

---

## Contributing

Contributions, bug reports, and feature requests are welcome!

- **Check Issues:** Search existing issues before submitting.
- **Open an Issue:** For bugs or ideas, include steps to reproduce, version, OS, and logs if possible.
- **Pull Requests:** Fork, branch, commit, and submit with a clear description.

---

## License

StreamWatch is open-source software licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgements

- Built on [Streamlink](https://streamlink.github.io/)
- UI powered by [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/) and [Rich](https://rich.readthedocs.io/en/stable/)

---

Happy Streaming! 📺




