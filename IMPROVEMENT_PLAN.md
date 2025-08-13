# StreamWatch CLI Improvement Plan

## Overview
This document outlines a comprehensive step-by-step plan to improve the StreamWatch CLI project based on the architectural review. Each task includes detailed implementation steps and acceptance criteria.

---

## Phase 1: Foundation & Setup (Priority: High)

### 1.1 Development Environment Setup
- [ ] **Setup Development Tools**
  - [ ] Add `pre-commit` hooks configuration
    - [ ] Create `.pre-commit-config.yaml`
    - [ ] Configure `black`, `isort`, `flake8`, `mypy`
    - [ ] Install and test pre-commit hooks
  - [ ] Add development dependencies to `pyproject.toml`
    - [ ] Add `black`, `isort`, `flake8`, `mypy`
    - [ ] Add `pytest-cov`, `pytest-mock`, `pytest-asyncio`
    - [ ] Add `pre-commit`, `bandit` for security
  - [ ] Create development documentation
    - [ ] Update `README.md` with development setup instructions
    - [ ] Create `CONTRIBUTING.md` with coding standards

### 1.2 Type Safety Implementation
- [ ] **Add Type Hints Throughout Codebase**
  - [ ] Create data models with `dataclasses` or `pydantic`
    - [ ] Create `src/streamwatch/models.py`
    - [ ] Define `StreamInfo`, `StreamStatus`, `PlaybackSession` models
    - [ ] Add validation and serialization methods
  - [ ] Add type hints to existing modules (in order):
    - [ ] `src/streamwatch/stream_utils.py` - URL parsing functions
    - [ ] `src/streamwatch/config.py` - Configuration functions
    - [ ] `src/streamwatch/storage.py` - Storage operations
    - [ ] `src/streamwatch/stream_checker.py` - Stream checking functions
    - [ ] `src/streamwatch/player.py` - Player operations
    - [ ] `src/streamwatch/ui.py` - UI functions
    - [ ] `src/streamwatch/core.py` - Core application logic
  - [ ] Configure `mypy` and fix all type errors
    - [ ] Create `mypy.ini` configuration
    - [ ] Run `mypy` and resolve all issues
    - [ ] Add `mypy` to CI pipeline

### 1.3 Enhanced Testing Framework
- [ ] **Expand Test Suite**
  - [ ] Setup comprehensive test structure
    - [ ] Create `tests/unit/` directory
    - [ ] Create `tests/integration/` directory
    - [ ] Create `tests/fixtures/` for test data
    - [ ] Setup `conftest.py` with common fixtures
  - [ ] Add unit tests for each module:
    - [ ] `tests/unit/test_config.py` - Configuration management
    - [ ] `tests/unit/test_storage.py` - Storage operations
    - [ ] `tests/unit/test_stream_utils.py` - Expand existing tests
    - [ ] `tests/unit/test_stream_checker.py` - Stream checking logic
    - [ ] `tests/unit/test_player.py` - Player operations
    - [ ] `tests/unit/test_ui.py` - UI components
  - [ ] Add integration tests:
    - [ ] `tests/integration/test_stream_workflow.py` - End-to-end workflows
    - [ ] `tests/integration/test_config_loading.py` - Configuration loading
  - [ ] Setup test coverage reporting
    - [ ] Configure `pytest-cov` in `pytest.ini`
    - [ ] Set minimum coverage threshold (80%)
    - [ ] Add coverage reporting to CI

---

## Phase 2: Code Organization & Architecture (Priority: High)

### 2.1 Refactor Core Module
- [ ] **Break Down Large Core Module**
  - [ ] Create new focused modules:
    - [ ] Create `src/streamwatch/menu_handler.py`
      - [ ] Extract menu display logic from `core.py`
      - [ ] Extract user input processing logic
      - [ ] Create `MenuHandler` class with methods:
        - [ ] `display_main_menu()`
        - [ ] `handle_user_input()`
        - [ ] `process_menu_choice()`
    - [ ] Create `src/streamwatch/stream_manager.py`
      - [ ] Extract stream CRUD operations from `core.py`
      - [ ] Create `StreamManager` class with methods:
        - [ ] `add_streams()`
        - [ ] `remove_streams()`
        - [ ] `list_streams()`
        - [ ] `import_streams()`
        - [ ] `export_streams()`
    - [ ] Create `src/streamwatch/playback_controller.py`
      - [ ] Extract playback session management from `core.py`
      - [ ] Create `PlaybackController` class with methods:
        - [ ] `start_playback_session()`
        - [ ] `handle_playback_controls()`
        - [ ] `stop_playback()`
  - [ ] Refactor `core.py` to use new modules:
    - [ ] Update `run_interactive_loop()` to delegate to new classes
    - [ ] Reduce `core.py` to orchestration logic only
    - [ ] Update imports and dependencies
  - [ ] Update tests for refactored modules
    - [ ] Create tests for new `MenuHandler` class
    - [ ] Create tests for new `StreamManager` class
    - [ ] Create tests for new `PlaybackController` class

### 2.2 Separate UI Concerns
- [ ] **Refactor UI Module**
  - [ ] Separate presentation from input handling:
    - [ ] Create `src/streamwatch/ui/display.py` for presentation
      - [ ] Move display functions (`display_main_menu`, `show_message`, etc.)
      - [ ] Keep only rendering logic
    - [ ] Create `src/streamwatch/ui/input_handler.py` for input processing
      - [ ] Move input functions (`prompt_main_menu_action`, etc.)
      - [ ] Add input validation and sanitization
    - [ ] Update `src/streamwatch/ui/__init__.py` to expose clean interface
  - [ ] Create UI abstraction layer:
    - [ ] Define `UIInterface` protocol/abstract class
    - [ ] Implement `ConsoleUI` class using Rich
    - [ ] Allow for future UI implementations (e.g., TUI with textual)

### 2.3 Implement Design Patterns
- [ ] **Add Command Pattern**
  - [ ] Create `src/streamwatch/commands/` directory
  - [ ] Create base `Command` class in `src/streamwatch/commands/base.py`
  - [ ] Implement specific commands:
    - [ ] `AddStreamCommand` - Add stream functionality
    - [ ] `RemoveStreamCommand` - Remove stream functionality
    - [ ] `PlayStreamCommand` - Play stream functionality
    - [ ] `RefreshStreamsCommand` - Refresh stream status
    - [ ] `ExportStreamsCommand` - Export streams functionality
  - [ ] Create `CommandInvoker` class to execute commands
  - [ ] Update menu handler to use command pattern

- [ ] **Add Dependency Injection**
  - [ ] Create `src/streamwatch/container.py` for dependency injection
  - [ ] Create `StreamWatchApp` main application class
  - [ ] Refactor modules to accept dependencies via constructor
  - [ ] Update `main.py` to use dependency injection

---

## Phase 3: Error Handling & Resilience (Priority: High)

### 3.1 Enhanced Error Handling
- [ ] **Improve Subprocess Error Handling**
  - [ ] Create `src/streamwatch/exceptions.py` for custom exceptions:
    - [ ] `StreamlinkError` - Base streamlink error
    - [ ] `StreamNotFoundError` - Stream not available
    - [ ] `NetworkError` - Network connectivity issues
    - [ ] `AuthenticationError` - Authentication failures
    - [ ] `TimeoutError` - Operation timeout
  - [ ] Enhance `stream_checker.py`:
    - [ ] Add detailed error categorization in `is_stream_live_for_check()`
    - [ ] Parse stderr/stdout for specific error types
    - [ ] Return structured error information
  - [ ] Add error recovery strategies:
    - [ ] Implement retry logic with exponential backoff
    - [ ] Add circuit breaker pattern for failing streams
    - [ ] Create `src/streamwatch/resilience.py` module

### 3.2 Caching & Performance
- [ ] **Implement Stream Status Caching**
  - [ ] Create `src/streamwatch/cache.py` module:
    - [ ] Implement `StreamStatusCache` class
    - [ ] Add TTL (Time To Live) for cache entries
    - [ ] Add cache invalidation strategies
  - [ ] Integrate caching in `stream_checker.py`:
    - [ ] Check cache before making streamlink calls
    - [ ] Update cache with fresh results
    - [ ] Handle cache misses gracefully
  - [ ] Add cache configuration options:
    - [ ] Add cache settings to `config.py`
    - [ ] Allow users to configure cache TTL
    - [ ] Add cache clear functionality

### 3.3 Rate Limiting & API Protection
- [ ] **Implement Rate Limiting**
  - [ ] Create `src/streamwatch/rate_limiter.py`:
    - [ ] Implement token bucket algorithm
    - [ ] Add per-platform rate limiting
    - [ ] Add global rate limiting
  - [ ] Integrate rate limiting in stream checking:
    - [ ] Apply rate limits before streamlink calls
    - [ ] Handle rate limit exceeded scenarios
    - [ ] Add rate limit status to UI

---

## Phase 4: Data Management & Validation (Priority: Medium)

### 4.1 Enhanced Data Models
- [ ] **Implement Pydantic Models**
  - [ ] Install and configure `pydantic`
  - [ ] Create comprehensive data models in `models.py`:
    - [ ] `StreamInfo` with validation
    - [ ] `StreamStatus` with status tracking
    - [ ] `PlaybackSession` with session data
    - [ ] `AppConfig` with configuration validation
  - [ ] Add data serialization/deserialization:
    - [ ] JSON serialization for storage
    - [ ] Validation on data loading
    - [ ] Migration support for model changes

### 4.2 Database Integration (Optional)
- [ ] **Consider SQLite Integration**
  - [ ] Evaluate benefits vs JSON storage
  - [ ] If proceeding:
    - [ ] Create `src/streamwatch/database.py`
    - [ ] Design database schema
    - [ ] Implement migration system
    - [ ] Add database operations
    - [ ] Create migration from JSON to SQLite

### 4.3 Input Validation & Security
- [ ] **Enhanced Input Validation**
  - [ ] Install `validators` library
  - [ ] Create `src/streamwatch/validators.py`:
    - [ ] URL validation and sanitization
    - [ ] Alias validation (length, characters)
    - [ ] File path validation
  - [ ] Add input sanitization throughout:
    - [ ] Sanitize URLs before processing
    - [ ] Validate user inputs in UI
    - [ ] Add XSS protection for display

---

## Phase 5: Performance & Scalability (Priority: Medium)

### 5.1 Asynchronous Operations
- [ ] **Implement Async I/O**
  - [ ] Add `asyncio` support to the project:
    - [ ] Install `aiofiles` for async file operations
    - [ ] Add `httpx` for async HTTP requests
  - [ ] Refactor storage operations:
    - [ ] Convert `storage.py` functions to async
    - [ ] Update `load_streams()` and `save_streams()` to be async
    - [ ] Add async context managers for file operations
  - [ ] Refactor stream checking:
    - [ ] Convert `stream_checker.py` to use async subprocess
    - [ ] Implement async batch processing
    - [ ] Add async timeout handling
  - [ ] Update application flow:
    - [ ] Convert main loop to async
    - [ ] Update UI to handle async operations
    - [ ] Add progress indicators for long operations

### 5.2 Lazy Loading & Pagination
- [ ] **Implement Lazy Loading**
  - [ ] Add lazy loading for large stream lists:
    - [ ] Create `StreamListManager` class
    - [ ] Implement pagination in UI
    - [ ] Add search/filter functionality
  - [ ] Optimize memory usage:
    - [ ] Load stream metadata on demand
    - [ ] Implement LRU cache for frequently accessed streams
    - [ ] Add memory usage monitoring

### 5.3 Background Processing
- [ ] **Add Background Tasks**
  - [ ] Create background stream monitoring:
    - [ ] Implement periodic stream status updates
    - [ ] Add notification system for stream status changes
    - [ ] Create background task scheduler
  - [ ] Add background cache warming:
    - [ ] Pre-fetch popular stream statuses
    - [ ] Update cache in background
    - [ ] Implement smart prefetching

---

## Phase 6: Configuration & Logging (Priority: Medium)

### 6.1 Advanced Configuration Management
- [ ] **Enhanced Configuration System**
  - [ ] Add configuration validation:
    - [ ] Use Pydantic for config validation
    - [ ] Add environment variable support
    - [ ] Create configuration schema
  - [ ] Add environment-specific configs:
    - [ ] Support for dev/prod configurations
    - [ ] Add configuration profiles
    - [ ] Implement config inheritance
  - [ ] Add hot-reloading:
    - [ ] Watch config file for changes
    - [ ] Reload configuration without restart
    - [ ] Add config change notifications

### 6.2 Structured Logging
- [ ] **Implement Structured Logging**
  - [ ] Install and configure `structlog`:
    - [ ] Add structured logging configuration
    - [ ] Create custom log processors
    - [ ] Add contextual logging
  - [ ] Enhance logging throughout:
    - [ ] Add structured logs with context
    - [ ] Include performance metrics
    - [ ] Add user action tracking
  - [ ] Add log analysis tools:
    - [ ] Create log parsing utilities
    - [ ] Add performance monitoring
    - [ ] Implement error tracking

---

## Phase 7: CI/CD & Automation (Priority: Medium)

### 7.1 GitHub Actions Pipeline
- [ ] **Setup Comprehensive CI/CD**
  - [ ] Create `.github/workflows/ci.yml`:
    - [ ] Test on Python 3.8, 3.9, 3.10, 3.11, 3.12
    - [ ] Test on Ubuntu, macOS, Windows
    - [ ] Run linting, type checking, tests
    - [ ] Generate coverage reports
  - [ ] Add security scanning:
    - [ ] Integrate `bandit` for security analysis
    - [ ] Add dependency vulnerability scanning
    - [ ] Implement SAST (Static Application Security Testing)
  - [ ] Setup automated releases:
    - [ ] Create release workflow
    - [ ] Automate PyPI publishing
    - [ ] Generate release notes

### 7.2 Quality Gates
- [ ] **Implement Quality Controls**
  - [ ] Add quality gates:
    - [ ] Minimum test coverage (80%)
    - [ ] No high-severity security issues
    - [ ] All type checks pass
    - [ ] All linting checks pass
  - [ ] Add automated code review:
    - [ ] Setup CodeQL analysis
    - [ ] Add automated dependency updates
    - [ ] Implement code quality metrics

---

## Phase 8: Documentation & User Experience (Priority: Low)

### 8.1 API Documentation
- [ ] **Generate API Documentation**
  - [ ] Setup Sphinx documentation:
    - [ ] Install and configure Sphinx
    - [ ] Create documentation structure
    - [ ] Generate API docs from docstrings
  - [ ] Add comprehensive docstrings:
    - [ ] Document all public functions
    - [ ] Add usage examples
    - [ ] Include type information
  - [ ] Create user guides:
    - [ ] Installation guide
    - [ ] Configuration guide
    - [ ] Troubleshooting guide

### 8.2 Enhanced User Interface
- [ ] **Improve Terminal UI**
  - [ ] Add advanced UI features:
    - [ ] Progress bars for long operations
    - [ ] Better error message formatting
    - [ ] Interactive help system
  - [ ] Add accessibility features:
    - [ ] Keyboard navigation improvements
    - [ ] Screen reader compatibility
    - [ ] Color blind friendly themes
  - [ ] Consider TUI framework:
    - [ ] Evaluate `textual` for rich TUI
    - [ ] Create prototype TUI interface
    - [ ] Add TUI as optional interface

---

## Phase 9: Advanced Features (Priority: Low)

### 9.1 Plugin System
- [ ] **Implement Plugin Architecture**
  - [ ] Create plugin interface:
    - [ ] Define plugin API
    - [ ] Create plugin loader
    - [ ] Add plugin configuration
  - [ ] Add example plugins:
    - [ ] Custom platform support
    - [ ] Notification plugins
    - [ ] Export format plugins

### 9.2 Advanced Stream Management
- [ ] **Enhanced Stream Features**
  - [ ] Add stream categories/tags:
    - [ ] Implement tagging system
    - [ ] Add category filtering
    - [ ] Create smart playlists
  - [ ] Add stream analytics:
    - [ ] Track viewing history
    - [ ] Generate usage statistics
    - [ ] Add recommendation system

---

## Implementation Guidelines

### Priority Order
1. **Phase 1**: Foundation & Setup (Essential for all other work)
2. **Phase 2**: Code Organization (Enables easier development)
3. **Phase 3**: Error Handling (Critical for reliability)
4. **Phase 4-6**: Core improvements (Can be done in parallel)
5. **Phase 7-9**: Polish and advanced features

### Testing Strategy
- [ ] Write tests BEFORE implementing new features
- [ ] Maintain minimum 80% code coverage
- [ ] Add integration tests for critical workflows
- [ ] Test on multiple platforms and Python versions

### Documentation Requirements
- [ ] Update docstrings for all new/modified functions
- [ ] Update README.md with new features
- [ ] Create migration guides for breaking changes
- [ ] Document configuration options

### Code Review Checklist
- [ ] All tests pass
- [ ] Code coverage maintained
- [ ] Type hints added
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance impact assessed

---

## Success Metrics

### Code Quality
- [ ] Test coverage ≥ 80%
- [ ] Zero high-severity security issues
- [ ] All type checks pass
- [ ] Consistent code style

### Performance
- [ ] Stream checking time < 5 seconds for 20 streams
- [ ] Application startup time < 2 seconds
- [ ] Memory usage < 50MB for typical usage

### User Experience
- [ ] Zero crashes in normal usage
- [ ] Clear error messages for all failure cases
- [ ] Responsive UI (no blocking operations)
- [ ] Comprehensive help documentation

---

## Notes

- Each checkbox represents a discrete, testable unit of work
- Estimated effort: 2-3 months for full implementation
- Can be implemented incrementally without breaking existing functionality
- Consider creating feature branches for each phase
- Regular code reviews recommended for architectural changes
