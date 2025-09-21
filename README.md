# StreamWatch: Your Lightweight CLI Live Stream Companion

[![PyPI version](https://img.shields.io/pypi/v/streamwatch.svg)](https://pypi.org/project/streamwatch/)
[![Python Versions](https://img.shields.io/pypi/pyversions/streamwatch.svg)](https://pypi.org/project/streamwatch/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/snowballons/streamwatch-cli.svg?style=social)](https://github.com/snowballons/streamwatch-cli)

<p align="center">
  <img src="assets/Images/logoign.png" alt="StreamWatch Logo" width="150"/>
</p>

**StreamWatch** is a modern, fast, and powerful command-line tool for managing and watching your favorite live streams—all without the resource drain of a web browser. It provides a rich terminal interface to see who's online, what they're streaming, and lets you jump right into the action.

<p align="center">
  <img src="assets/Images/streamwatch-cli.gif" alt="StreamWatch CLI in action" width="700"/>
  <br/>
  <em>(Demo showcasing StreamWatch's interactive menu and playback)</em>
</p>

---

## Table of Contents

*   [Why Use StreamWatch?](#why-use-streamwatch)
*   [Key Features](#key-features)
*   [Architecture & Recent Improvements](#architecture--recent-improvements)
*   [Supported Platforms](#supported-platforms)
*   [Prerequisites](#prerequisites)
*   [Installation](#installation)
*   [Getting Started](#getting-started)
*   [Usage](#usage)
    *   [Main Menu](#main-menu)
    *   [Playback Controls](#playback-controls)
*   [Advanced Configuration](#advanced-configuration)
    *   [Stream Aliases](#stream-aliases)
    *   [Using a `streams.d` Directory](#using-a-streamsd-directory)
    *   [Importing & Exporting](#importing--exporting)
    *   [Playback Hooks](#playback-hooks)
*   [Configuration File](#configuration-file)
*   [Development Setup](#development-setup)
*   [Troubleshooting](#troubleshooting)
*   [Contributing](#contributing)
*   [License](#license)
*   [Acknowledgements](#acknowledgements)

---

## Why Use StreamWatch?

*   **Lightweight & Fast:** Consumes a fraction of the CPU and RAM compared to a browser.
*   **Focus-Friendly:** A clean, distraction-free interface.
*   **Efficient Workflow:** Manage and launch streams from a single, keyboard-driven interface.
*   **Highly Customizable:** Tailor StreamWatch to your needs with custom settings and automation hooks.
*   **Broad Platform Support:** Works with hundreds of sites out of the box, powered by Streamlink.
*   **Cross-Platform:** A consistent experience on Windows, macOS, and Linux.

---

## Key Features

- **Live Status Display:** See who's live with their Alias/Username, Platform, Category, and Viewer Count.
- **Interactive Navigation:** Use arrow keys, number input, or first-letter search to quickly select streams.
- **Playback Controls:** Replay, play next/previous, change quality, and more, all from the terminal.
- **Stream Aliases:** Assign custom nicknames to your streams for a personalized list.
- **Stream Management:** Add, remove, list, import, and export your stream list with ease.
- **File-Based Management:** Use a `streams.d` directory to manage your streams with simple text files.
- **Background Recording:** Record live streams to a file while you continue to browse or watch other streams.
- **Automatic Reconnection:** Automatically attempts to reconnect if a stream drops.
- **Playback Hooks:** Trigger custom scripts before and after a stream plays.
- **Persistent Configuration:** User-editable `config.ini` for settings and `streams.json` for your interactive list.
- **Quick Access:** Instantly replay the last stream you watched.
- **Polished UI:** A colorful and modern terminal interface with enhanced pagination and input handling.
- **Detailed Logging:** Comprehensive log files for easy troubleshooting.
- **Enhanced Resilience:** Built-in retry mechanisms, circuit breaker patterns, and intelligent caching for improved reliability.
- **Modular Architecture:** Clean separation of concerns with dedicated modules for UI, stream management, and playback control.

---

## Architecture & Recent Improvements

StreamWatch has undergone significant architectural improvements to enhance reliability, maintainability, and performance:

### 🏗️ **Modular Architecture**
- **Separation of Concerns:** Clean division between UI components, stream management, and playback control
- **Command Pattern:** Structured command system for better code organization and testing
- **Dependency Injection:** Improved modularity and testability through proper dependency management
- **Enhanced Models:** Comprehensive data models with validation using Pydantic for type safety

### 🔄 **Resilience & Performance**
- **Intelligent Caching:** Stream status caching with TTL to reduce API calls and improve response times
- **Retry Mechanisms:** Exponential backoff retry logic for handling temporary failures
- **Circuit Breaker Pattern:** Prevents cascading failures by temporarily disabling failing streams
- **Rate Limiting:** Token bucket algorithm to respect platform rate limits and prevent abuse

### 🛡️ **Security & Validation**
- **Enhanced Input Validation:** Comprehensive URL and user input sanitization
- **Security Scanning:** Integrated Bandit security vulnerability scanning in CI/CD
- **XSS Protection:** Safe rendering of user content and stream metadata
- **Input Sanitization:** Proper validation and cleaning of all user inputs

### 🧪 **Testing & Quality Assurance**
- **Comprehensive Test Suite:** Unit and integration tests with high coverage requirements
- **Type Safety:** Full type hints throughout the codebase with MyPy static type checking
- **Code Quality Tools:** Black, isort, Flake8, and MyPy integrated via pre-commit hooks
- **Automated Testing:** CI/CD pipeline with automated quality checks and security scanning

### 📊 **Enhanced User Experience**
- **Improved Pagination:** Better handling of large stream lists with efficient navigation
- **Enhanced Error Handling:** More informative error messages and graceful failure recovery
- **Better Logging:** Comprehensive logging system for easier troubleshooting and debugging
- **UI Responsiveness:** Optimized UI components for smoother interaction and better performance

### 🔧 **Developer Experience**
- **Modern Development Tools:** Integration with uv for faster dependency management
- **Pre-commit Hooks:** Automated code quality checks before commits
- **Development Documentation:** Comprehensive setup and contribution guidelines
- **Consistent Coding Standards:** Enforced code formatting and style guidelines

These improvements ensure StreamWatch remains maintainable, secure, and performant while providing an excellent user experience.

---

## Supported Platforms

StreamWatch uses **[Streamlink](https://streamlink.github.io/)**, so it can play streams from any platform Streamlink supports. Enhanced display features (Username, Platform, Category, Viewer Count) are available for over 20 popular platforms, including:

*   YouTube, Twitch, Kick, TikTok
*   BiliBili, Douyin, Huya, Vimeo, Dailymotion
*   PlutoTV, BBC iPlayer, ARD/ZDF Mediathek, RaiPlay, RTVE Play, Atresplayer, Mitele
*   AbemaTV, Adult Swim, Bloomberg, Bigo Live, and more.

A generic fallback is used for other platforms.

---

## Prerequisites

- **Python 3.7+**
- **Streamlink** (installed automatically with StreamWatch)
- **MPV Media Player** ([Download](https://mpv.io/)) - **Highly recommended**

---

## Installation

Install StreamWatch using `pip`:

```bash
pip install streamwatch
```

<details>
<summary><b>Alternative: Installation from Source</b></summary>

```bash
# 1. Clone the repository
git clone https://github.com/snowballons/streamwatch-cli.git
cd streamwatch-cli

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Run StreamWatch
streamwatch
```
</details>

---

## Getting Started

1.  **Run StreamWatch for the first time:**
    ```bash
    streamwatch
    ```
    This will create the configuration directory and files.

2.  **Add streams:**
    - Press `A` in the main menu to add a stream.
    - Enter a stream URL. To add a custom alias, type it after the URL (e.g., `https://twitch.tv/shroud The FPS King`).
    - To add multiple streams, separate them with commas.

3.  **Refresh and watch:**
    - Press `F` to refresh the stream list and see who's live.
    - Select a stream to start watching.

---

## Usage

### Main Menu

| Key(s) | Action                                       |
|--------|----------------------------------------------|
| `Enter`  | Open interactive selection for live streams. |
| `[Number]` | Play a live stream directly by its number.   |
| `L`      | List all configured streams.                 |
| `A`      | Add new streams (with optional aliases).     |
| `R`      | Remove streams from your list.               |
| `I`      | Import streams from a `.txt` file.           |
| `E`      | Export your stream list to a `.json` file.   |
    | `V`      | Open Recording Controls menu.                |
| `P`      | Play the last stream you watched.            |
| `F`      | Force a refresh of the live stream list.     |
| `Q`      | Quit StreamWatch.                            |

### Playback Controls

| Key(s) | Action                                         |
|--------|------------------------------------------------|
| `S`      | Replay the current stream.                     |
| `N`      | Play the next live stream in the list.         |
| `P`      | Play the previous live stream in the list.     |
| `C`      | Change quality on the fly.                     |
| `M`      | Stop stream and return to the main menu.       |
| `D`      | Open the developer donation link in your browser.|
| `Q`      | Stop stream and quit StreamWatch.              |

---

## Advanced Configuration

### Stream Aliases

Assign custom names to your streams for easier identification. When adding a stream, type the alias after the URL:

```
URL(s) [and optional alias(es)]: https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw Linus Tech Tips
```

### Using a `streams.d` Directory

For advanced stream management, create a `streams.d` directory in your StreamWatch config folder. Inside this directory, create any number of text files (e.g., `gaming.list`, `news.txt`) and add one stream URL per line.

StreamWatch will load all streams from `streams.json` and any files in `streams.d` at startup.

**Note:** The `A` (Add) and `R` (Remove) commands only affect `streams.json`. To manage streams in `streams.d`, you must edit the files directly.

### Importing & Exporting

- **Import (`I`):** Bulk-add streams from any `.txt` file (one URL per line).
- **Export (`E`):** Create a backup of your current stream list (including aliases) to a `.json` file.

### Playback Hooks

Automate your environment by running custom scripts before and after a stream plays.

1.  Create an executable script (e.g., `start_stream.sh`, `end_stream.bat`).
2.  Set the full path to your script in `config.ini` under `pre_playback_hook` or `post_playback_hook`.

StreamWatch passes the following arguments to your script: `url`, `alias`, `username`, `platform`, `quality`.

**Example `hook.sh`:**

```bash
#!/bin/bash
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Event for alias '$2' on platform '$4' with quality '$5'" >> ~/stream_events.log
```

---

## Configuration File

Your settings and stream lists are stored in your user configuration directory:

- **Linux/macOS:** `~/.config/streamwatch/`
- **Windows:** `%APPDATA%\\StreamWatch\\`

The `config.ini` file is created on the first run and can be edited to customize StreamWatch's behavior.

---

## Development Setup

If you want to contribute to StreamWatch or run it from source, follow these steps:

### Prerequisites for Development

- **Python 3.8+**
- **uv** (recommended) or **pip**
- **Git**

### Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/snowballons/streamwatch-cli.git
   cd streamwatch-cli
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   # Install all dependencies including development tools
   uv sync --dev

   # Or using the dependency groups
   uv sync --group dev
   ```

   **Alternative with pip:**
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install in editable mode with dev dependencies
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks:**
   ```bash
   # Using uv
   uv run pre-commit install

   # Or with pip
   pre-commit install
   ```

4. **Run the development version:**
   ```bash
   # Using uv
   uv run streamwatch

   # Or with pip (after activating venv)
   streamwatch
   ```

### Development Tools

The project includes several development tools configured via pre-commit hooks:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/streamwatch --cov-report=html

# Run specific test file
uv run pytest tests/test_stream_utils.py
```

### Code Quality Checks

```bash
# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run specific tools
uv run black src/ tests/
uv run isort src/ tests/
uv run flake8 src/ tests/
uv run mypy src/
uv run bandit -r src/
```

---

## Troubleshooting

Log files are located in the `logs/` subdirectory of your config folder. These logs contain detailed debug information that can help diagnose problems.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for more details.

---

## License

StreamWatch is open-source software licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgements

StreamWatch is built upon these excellent open-source projects:

- [Streamlink](https://streamlink.github.io/)
- [Rich](https://github.com/Textualize/rich)
- [Python Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)

Happy Streaming! 📺
