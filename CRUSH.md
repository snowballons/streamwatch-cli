# StreamWatch Development Guide

This guide provides commands and style guidelines for `streamwatch-cli`.

## Commands

- **Run:** `uv run streamwatch`
- **Install Dev Dependencies:** `uv sync --dev`
- **Lint & Format:**
  - `uv run black src/ tests/`
  - `uv run isort src/ tests/`
  - `uv run flake8 src/ tests/`
- **Type Check:** `uv run mypy src/`
- **Test:**
  - **All:** `uv run pytest`
  - **Single File:** `uv run pytest tests/unit/test_config.py`
  - **With Coverage:** `uv run pytest --cov=src/streamwatch --cov-report=html`
- **Pre-commit Hooks:** `uv run pre-commit run --all-files`

## Code Style

- **Formatting:** Use `black` for code formatting and `isort` for organizing imports.
- **Imports:** Group imports into standard library, third-party, and application-specific modules.
- **Typing:** Use type hints for all function signatures. Run `mypy` to verify.
- **Naming:**
  - Classes: `PascalCase`
  - Functions/Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:** Use `try...except` blocks for operations that can fail (e.g., I/O, network requests). Log exceptions with context.
- **Docstrings:** Use Google-style docstrings.
- **Logging:** Use the `logging` module. Get a logger instance with `logging.getLogger(__name__)`.
