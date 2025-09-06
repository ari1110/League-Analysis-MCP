---
created: 2025-09-04T19:09:18Z
last_updated: 2025-09-04T23:12:23Z
version: 1.2
author: Claude Code PM System
---

# Technology Context

## Primary Technology Stack

### Core Runtime
- **Python 3.10+** - Minimum supported version
- **UV Package Manager** - Modern Python package and dependency management
- **AsyncIO** - Asynchronous programming for MCP protocol support

### Development & Version Control
- **Git** - Primary version control with worktree support
- **Jujutsu (jj) v0.33.0+** - Advanced VCS for parallel development workflows
  - **Colocated with Git** for seamless integration (`jj git init --colocate`)
  - **True parallel agent execution** through isolated working copies
  - **Conflict-free parallel development** - working copies as commits
  - **Superior safety** - `jj undo` reverses any operation, non-destructive rebase
  - **No merge conflicts** - automatic conflict resolution with smart rebasing
  - **Key commands**: `jj new`, `jj edit`, `jj rebase -r`, `jj log --graph`
  - **Breakthrough capability**: Enabled 74 pyright error fixes across 6 files simultaneously
  - **Agent integration**: Each Task tool call creates isolated `jj new` working copy

### Key Framework Dependencies

#### MCP Framework
- **FastMCP 2.0** - High-level Model Context Protocol framework
  - Primary framework for MCP server implementation
  - Provides decorators for tools (`@mcp.tool()`) and resources (`@mcp.resource()`)
  - Handles MCP protocol communication over stdio transport

#### Yahoo API Integration
- **YFPY 16.0+** - Yahoo Fantasy Sports Python wrapper
  - Primary interface to Yahoo Fantasy Sports API
  - Handles OAuth token management and API requests
  - Provides structured data models for fantasy sports entities

#### Data Processing & Validation
- **Pydantic 2.0+** - Data validation and settings management
  - Type-safe data models throughout application
  - Configuration validation and parsing
  - API response validation and transformation

- **Pandas 2.0+** - Data analysis and transformation
  - Historical data processing and aggregation
  - Statistical analysis for manager profiling
  - Draft strategy analysis and pattern recognition

#### Authentication & Security
- **Cryptography 3.0+** - SSL certificate generation for OAuth callback server
  - Self-signed certificate generation for localhost HTTPS
  - Required for automated OAuth flow with callback server

- **python-dotenv 1.0.0+** - Environment variable management
  - OAuth token storage and configuration
  - Development environment setup

#### HTTP & Network
- **Requests 2.31.0+** - HTTP client for Yahoo API calls
  - Reliable HTTP request handling
  - Session management and connection pooling

- **asyncio-throttle 1.0.0+** - Rate limiting for API requests
  - Respect Yahoo API rate limits (60 requests/minute)
  - Prevent API quota exhaustion

### Development & Quality Tools

#### Code Quality & Type Checking
- **Pyright 1.1.405+** - Fast type checker with superior inference (development)
- **MyPy 1.17.1+** - Strict static type checking (CI/CD)
- **Flake8 7.1.1+** - Code style linting
- **Black 23.0.0+** (dev) - Code formatter
- **isort 5.12.0+** (dev) - Import sorting
- **types-requests** - Type stubs for external dependencies

#### Testing Framework
- **pytest 7.0.0+** - Primary testing framework
- **pytest-asyncio 0.21.0+** - AsyncIO testing support

#### Parallel Development Tools
- **Multiple Task Tool Calls** - Simultaneous agent execution for true parallelism
- **Jujutsu Working Copies** - Isolated parallel development environments via `jj new`
  - **Core workflow**: `jj new -m "task-description"` → parallel work → `jj rebase -r <commit> -d main`
  - **Visual monitoring**: `jj log --graph` and `jj log -r 'heads()'` for progress tracking
  - **Safety features**: `jj undo` for operation reversal, `jj abandon` for cleanup
  - **Git integration**: `jj git push` for seamless Git repository updates
- **repo-issue-fixer agent** - Automated systematic issue resolution with batch verification
- **Testable Architecture Pattern** - Private `_impl` functions + public API + MCP wrappers
- **Shared Utilities Module** - Centralized common functionality (shared_utils.py) eliminating code duplication
- **Verified Command Set** - 15+ verified Jujutsu commands for comprehensive parallel workflows

## Architecture Technologies

### Model Context Protocol (MCP)
- **Transport**: stdio (standard input/output)
- **Protocol Version**: MCP 1.0
- **Message Format**: JSON-RPC 2.0
- **Tool Discovery**: Dynamic via MCP protocol
- **Resource Access**: URI-based resource endpoints

### Authentication Architecture
- **OAuth 2.0** - Yahoo Developer API authentication
- **Authorization Code Flow** - Standard OAuth flow with PKCE
- **Token Storage** - Environment variables (not file-based)
- **Refresh Tokens** - Automatic token refresh handling
- **HTTPS Callback Server** - Local server for automated code capture

### Caching Technology
- **In-Memory Cache** - Python dictionary-based with TTL management
- **Cache Strategy**: 
  - Historical data: Permanent storage (TTL = -1)
  - Current season: 5-minute TTL (TTL = 300)
- **Size Management**: 100MB default limit with LRU eviction
- **Cache Keys**: Structured keys with sport, league, season, data type

### Data Processing Pipeline
- **Yahoo API** → **YFPY Wrapper** → **Pydantic Validation** → **Pandas Processing** → **Cache Storage** → **MCP Response**

## Deployment & Distribution

### Package Management
- **Build System**: Hatchling (PEP 517/518 compliant)
- **Distribution**: PyPI (Python Package Index)
- **Installation Methods**:
  - `uvx league-analysis-mcp-server` (recommended)
  - `pip install league-analysis-mcp-server` 
  - Development: `uv sync --all-extras`

### Runtime Environment
- **Execution Mode**: Command-line server via MCP protocol
- **Process Model**: Single-process, async event loop
- **Communication**: stdio transport (standard for MCP servers)
- **Configuration**: JSON files + environment variables
- **Logging**: Python logging to stderr (MCP compatible)

### CI/CD & Testing Technology
- **GitHub Actions** - Automated testing and publishing
- **Automated Publishing** - Tag-based release to PyPI (v0.3.0+ published successfully)
- **Version Management** - Synchronized between pyproject.toml and config files
- **Testing Matrix** - Python 3.10, 3.11, 3.12 compatibility

#### Comprehensive Testing Framework (v0.3.0+)
- **Functional Testing Suite** - 6 test files validating real user scenarios and workflows
- **Base Test Classes** - `FunctionalTestCase` and `IntegrationTestCase` with Yahoo API mocking
- **Test Fixtures** - Realistic Yahoo API response data in JSON format for consistent testing
- **Integration Testing** - Real Yahoo API testing with credential validation (`test_live_data.py`)
- **Test Runner** - `run_functional_tests.py` with environment checking and detailed reporting
- **Error Scenario Testing** - Comprehensive edge case and error condition validation

#### Static Analysis Integration
- **Ruff** - Python linting and code quality analysis
- **MyPy** - Static type checking with --ignore-missing-imports
- **Pylance** - IDE-based diagnostics via mcp__ide__getDiagnostics tool
- **Comprehensive Test Suite** - `tests/test_comprehensive.py` integrating all analysis tools
- **Windows Compatibility** - Unicode-safe testing output for cross-platform development

## Platform Support

### Operating Systems
- **Windows** - Primary development platform (MINGW64/Git Bash)
- **macOS** - Full support via UV and Python
- **Linux** - Full support via UV and Python

### MCP Client Compatibility  
- **Claude Desktop** - Primary target client
- **Claude Code** - IDE integration via MCP protocol
- **Continue.dev** - VS Code extension with MCP support
- **Custom Clients** - Any MCP 1.0 compatible client

### Browser Compatibility (OAuth)
- **Chrome/Edge** - Preferred for automated OAuth flow
- **Firefox** - Full support with SSL certificate handling
- **Safari** - Supported with manual certificate acceptance

## Version Management Strategy

### Semantic Versioning
- **Format**: MAJOR.MINOR.PATCH (e.g., 0.2.2)
- **Synchronization**: pyproject.toml and config/settings.json must match
- **Automation**: `bump_version.py` script maintains consistency
- **Release Tags**: Git tags trigger automated PyPI publishing

### Dependency Versioning
- **Minimum Versions**: Specified for core dependencies
- **Lock File**: `uv.lock` ensures reproducible builds
- **Update Strategy**: Regular updates with compatibility testing
- **Security Updates**: Prompt updates for security-related dependencies

## Performance Characteristics

### Caching Performance
- **Hit Rate**: ~95% for historical data (permanent cache)
- **Miss Penalty**: Yahoo API call + processing (1-3 seconds)
- **Memory Usage**: ~100MB typical, 100MB max (configurable)
- **Eviction**: LRU strategy for current season data

### API Rate Limiting
- **Yahoo API Limit**: 60 requests per minute
- **Implementation**: asyncio-throttle with burst handling
- **Strategy**: Aggressive caching to minimize API calls
- **Historical Analysis**: Batch processing with rate limit respect

### Startup Performance
- **Cold Start**: ~2-3 seconds (import and initialization)
- **Authentication Check**: ~500ms (cached token validation)
- **First Request**: ~1-2 seconds (cache warming)
- **Subsequent Requests**: ~50-200ms (cache hits)

## Development Environment

### Required Tools
1. **UV Package Manager** - `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Python 3.10+** - System Python or UV-managed
3. **Git** - Version control and repository management
4. **Yahoo Developer Account** - For OAuth credentials

### Optional Development Tools
- **VS Code** - IDE with Python and MCP extensions
- **Claude Code** - AI-assisted development with MCP integration
- **GitHub CLI** - Repository management and issue tracking
- **Postman/Insomnia** - API testing (though not directly applicable to MCP)

### Environment Setup
```bash
# Clone and setup
git clone https://github.com/ari1110/League-Analysis-MCP.git
cd League-Analysis-MCP
uv sync --all-extras

# Development commands
uv run python -m src.league_analysis_mcp_server  # Run server
uv run python test_server.py                     # Run tests
uv build                                         # Build package
```

## Security Considerations

### Authentication Security
- **OAuth 2.0**: Industry standard authentication
- **Token Storage**: Environment variables (not committed to git)
- **HTTPS Required**: All Yahoo API communication encrypted
- **Local Callback**: HTTPS localhost server for OAuth (self-signed certificate)

### Data Security
- **No Data Persistence**: Cache is in-memory only
- **API Key Protection**: Credentials never logged or exposed
- **Minimal Permissions**: OAuth scope limited to fantasy sports read access
- **Error Handling**: Sensitive information filtered from error messages

### Network Security
- **TLS 1.2+**: Required for all external API calls
- **Certificate Validation**: Enabled for all HTTPS requests
- **Local Server**: Callback server only active during OAuth flow
- **Port Management**: Uses standard port 8080 for OAuth callback