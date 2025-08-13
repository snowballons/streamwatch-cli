# Contributing to StreamWatch

Thank you for your interest in contributing to StreamWatch! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see [Development Setup](#development-setup))
4. Create a new branch for your changes
5. Make your changes and test them
6. Submit a pull request

## Development Setup

Please refer to the [Development Setup section in README.md](README.md#development-setup) for detailed instructions on setting up your development environment.

### Quick Setup Summary

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/streamwatch-cli.git
cd streamwatch-cli

# Install dependencies
uv sync --dev

# Set up pre-commit hooks
uv run pre-commit install

# Run tests to ensure everything works
uv run pytest
```

## Coding Standards

### Code Style

We use several tools to maintain consistent code quality:

- **Black** for code formatting (line length: 88 characters)
- **isort** for import sorting (compatible with Black)
- **Flake8** for linting and style checking
- **MyPy** for static type checking
- **Bandit** for security vulnerability scanning

### Pre-commit Hooks

All code must pass pre-commit hooks before being committed. The hooks will automatically:

- Format code with Black
- Sort imports with isort
- Check code style with Flake8
- Perform type checking with MyPy
- Scan for security issues with Bandit
- Check for common issues (trailing whitespace, large files, etc.)

Run hooks manually:
```bash
uv run pre-commit run --all-files
```

### Python Style Guidelines

1. **Follow PEP 8** with Black's formatting
2. **Use type hints** for all function parameters and return values
3. **Write docstrings** for all public functions, classes, and modules
4. **Use descriptive variable names** and avoid abbreviations
5. **Keep functions small** and focused on a single responsibility
6. **Use f-strings** for string formatting when possible

### Example Code Style

```python
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def process_stream_url(url: str, alias: Optional[str] = None) -> dict[str, str]:
    """Process a stream URL and return stream information.

    Args:
        url: The stream URL to process
        alias: Optional custom alias for the stream

    Returns:
        Dictionary containing stream information

    Raises:
        ValueError: If the URL is invalid
    """
    if not url.strip():
        raise ValueError("URL cannot be empty")

    result = {
        "url": url.strip(),
        "alias": alias or extract_default_name(url),
    }

    logger.info(f"Processed stream: {result['alias']}")
    return result
```

## Testing Guidelines

### Writing Tests

1. **Write tests for all new functionality**
2. **Use pytest** as the testing framework
3. **Use pytest-mock** for mocking external dependencies
4. **Aim for high test coverage** (target: >90%)
5. **Write both unit tests and integration tests**

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

from streamwatch.core import StreamProcessor


class TestStreamProcessor:
    """Test cases for StreamProcessor class."""

    def test_process_valid_url(self):
        """Test processing a valid stream URL."""
        processor = StreamProcessor()
        result = processor.process("https://twitch.tv/example")

        assert result["url"] == "https://twitch.tv/example"
        assert "alias" in result

    @patch("streamwatch.core.requests.get")
    def test_process_url_with_network_error(self, mock_get):
        """Test handling network errors during URL processing."""
        mock_get.side_effect = ConnectionError("Network error")

        processor = StreamProcessor()
        with pytest.raises(ConnectionError):
            processor.process("https://twitch.tv/example")
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/streamwatch --cov-report=html

# Run specific test file
uv run pytest tests/test_stream_utils.py

# Run tests matching a pattern
uv run pytest -k "test_process"
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Add or update tests** for your changes

4. **Ensure all tests pass**:
   ```bash
   uv run pytest
   uv run pre-commit run --all-files
   ```

5. **Commit your changes** with a clear commit message:
   ```bash
   git commit -m "Add feature: brief description of changes"
   ```

6. **Push to your fork** and create a pull request

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Pull Request Guidelines

- **Provide a clear description** of the changes
- **Link to related issues** using keywords (e.g., "Fixes #123")
- **Include screenshots** for UI changes
- **Update documentation** if necessary
- **Ensure CI passes** before requesting review

## Issue Reporting

When reporting bugs, please include:

1. **StreamWatch version** (`streamwatch --version`)
2. **Python version** (`python --version`)
3. **Operating system** and version
4. **Steps to reproduce** the issue
5. **Expected behavior** vs actual behavior
6. **Error messages** or logs (if any)
7. **Configuration files** (if relevant, remove sensitive data)

## Feature Requests

When requesting features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and why the feature would be valuable
3. **Provide examples** of how the feature would work
4. **Consider implementation complexity** and maintenance burden

## Questions?

If you have questions about contributing, feel free to:

- Open an issue with the "question" label
- Start a discussion in the GitHub Discussions tab
- Contact the maintainers directly

Thank you for contributing to StreamWatch! 🎉
