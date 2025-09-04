# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Essential Commands
```bash
# Install dependencies and build
uv sync --all-extras

# Run tests (all test files required for CI/CD)
uv run python test_server.py
uv run python test_auth.py
uv run python test_startup.py

# Run single test file
uv run python test_server.py

# Build package
uv build

# Run server locally for development
uv run python -m src.league_analysis_mcp_server

# Version management (keeps pyproject.toml and config/settings.json synchronized)
uv run python bump_version.py patch  # or minor/major
```

### Publishing Workflow
The repository uses automated publishing via GitHub Actions. To publish:
```bash
# Use the version bump script to maintain synchronization
python bump_version.py patch
git add . && git commit -m "chore: Bump version to X.Y.Z"
git tag vX.Y.Z && git push origin main && git push origin vX.Y.Z
```

Tag pushes automatically trigger the streamlined publish workflow (no TestPyPI, direct to PyPI + GitHub releases).

## Architecture Overview

### Core Framework
Built on **FastMCP 2.0** - a high-level Model Context Protocol framework. The server exposes Yahoo Fantasy Sports data through standardized MCP tools and resources.

### Key Architectural Components

**Server Entry Point** (`src/league_analysis_mcp_server/server.py`):
- FastMCP server initialization with configuration from `config/settings.json`
- Global app state containing auth manager, cache manager, config, and game ID mappings
- Tool and resource registration

**Authentication System** (`enhanced_auth.py` + `oauth_callback_server.py`):
- **Enhanced Auth Manager**: Primary OAuth handler with token refresh capabilities  
- **OAuth Callback Server**: Automated authorization code capture via HTTPS localhost server
- Uses `https://localhost:8080/` redirect URI (must match Yahoo Developer app)
- **Two OAuth Methods**: Manual (copy-paste code) and Automated (callback server)
- Conversational setup through MCP tools (check_setup_status, create_yahoo_app, etc.)
- Environment variable storage with .env support

**Caching Layer** (`cache.py`):
- **Historical data**: Permanent cache (TTL = -1)
- **Current season data**: 5-minute TTL (TTL = 300)
- Size-limited (100MB default) with smart eviction

**Tool Architecture**:
- **Basic tools** (`tools.py`): Current season data, league info, standings, rosters
- **Historical tools** (`historical.py`): Multi-season draft analysis, transaction history
- **Analytics tools** (`analytics.py`): Manager profiling, trade predictions, draft strategy analysis
- **Authentication tools** (`enhanced_auth.py`): Streamlined setup workflow

**Resource System** (`resources.py`):
- Read-only data access via URIs: `league_overview://`, `current_week://`, `manager_profiles://`
- Comprehensive data aggregation for AI analysis

### Data Flow Pattern
Request → Authentication Check → Cache Lookup → Yahoo API Call (if needed) → Analytics Processing → Cache Storage → Response

### Configuration System
- **`config/settings.json`**: Server metadata, feature flags, cache settings, rate limiting
- **`config/game_ids.json`**: Yahoo game ID mappings for historical seasons (2015-2024)
- **Version synchronization**: Both files must maintain matching version numbers

## Development Guidelines

### Authentication Development
- All new auth features should use the Enhanced Auth Manager
- **OAuth redirect URI**: `https://localhost:8080/` - must match Yahoo Developer app configuration exactly
- **Automated OAuth**: Preferred method using `start_automated_oauth_flow()` - creates HTTPS server to capture code
- **Manual OAuth**: Fallback using `start_oauth_flow()` + `complete_oauth_flow(code)` 
- **Token separation**: OAuth token exchange is isolated from YFPY connection testing for better debugging
- Use conversational MCP tools for user setup rather than command-line scripts

### OAuth Setup Methods
**Method 1: Automated (Recommended)**
```
1. save_yahoo_credentials(key, secret)
2. start_automated_oauth_flow()  # Opens browser, captures code automatically
```

**Method 2: Manual (Fallback)**  
```
1. save_yahoo_credentials(key, secret)
2. start_oauth_flow()  # Get authorization URL
3. Visit URL, get code manually
4. complete_oauth_flow(verification_code)
```

**Method 3: Connection Testing (Separate)**
```
5. test_yahoo_connection()  # Test YFPY integration after token exchange
```

### Caching Strategy
- Historical data (draft results, past seasons): Cache permanently
- Current/live data (standings, current week): Use short TTL
- Always check cache before making Yahoo API calls
- Use `clear_cache()` tool for development/debugging

### Yahoo API Integration
- All API calls go through `get_yahoo_query()` helper in tools.py
- Game IDs are automatically resolved from season + sport combination
- Rate limiting (60 req/min) is handled automatically
- Error handling should gracefully degrade when API is unavailable

### Testing Requirements
- All three test files (`test_server.py`, `test_auth.py`, `test_startup.py`) must pass for CI/CD
- Tests run without Yahoo credentials - they test core functionality and imports
- Use test files to verify package installation and import paths

### Multi-Sport Support
Supported sports: `nfl`, `nba`, `mlb`, `nhl`
- Each sport has game ID mappings for seasons 2015-2024
- Analytics algorithms are sport-agnostic where possible
- Historical analysis requires minimum 2 seasons of data

### Version Management
- **Critical**: `pyproject.toml` and `config/settings.json` versions must stay synchronized
- Use `bump_version.py` script to update both files atomically
- Publishing workflow extracts version from pyproject.toml for release tags
- Manual version edits will break the automated release process

### MCP Tool Development
- Use FastMCP decorators: `@mcp.tool()` for tools, `@mcp.resource()` for resources
- Tools should handle authentication errors with helpful messages
- Include proper type hints for all parameters and return values
- Cache expensive operations, especially multi-season historical queries

## OAuth Troubleshooting

### Common Issues and Solutions

**OAuth Timeout/Hanging Issues:**
- **Cause**: Usually redirect URI mismatch between code and Yahoo Developer app
- **Solution**: Ensure Yahoo app has `https://localhost:8080/` as redirect URI
- **Verification**: Check authorization URL contains correct redirect_uri parameter

**SSL Certificate Issues:**
- **Automated flow fails**: Install `cryptography` package: `uv add cryptography`
- **Certificate errors**: Browser may show security warnings for self-signed certificate (safe to proceed)
- **Port conflicts**: Ensure nothing else uses port 8080

**Yahoo Developer App Configuration:**
- **Redirect URI**: Must be exactly `https://localhost:8080/` (with trailing slash)
- **Alternative**: Can also register `urn:ietf:wg:oauth:2.0:oob` for manual flow
- **App Type**: Web Application (not mobile or desktop)

**Token Exchange Errors:**
- **400 Bad Request**: Usually redirect URI mismatch or expired code  
- **401 Unauthorized**: Invalid consumer key/secret
- **Network timeouts**: Check firewall/proxy settings

**Connection Test Failures:**
- **Expected behavior**: Connection test may fail even with valid tokens
- **YFPY requirements**: Needs additional token fields that Yahoo doesn't always provide
- **Workaround**: Token exchange success = OAuth working, connection test = YFPY compatibility

## Key Dependencies
- **FastMCP 2.0**: MCP framework
- **YFPY 16.0+**: Yahoo Fantasy Sports API wrapper  
- **Pydantic 2.0+**: Data validation and settings management
- **Pandas 2.0+**: Data analysis and transformation
- **Cryptography 3.0+**: SSL certificate generation for OAuth callback server
- **UV**: Package management and virtual environment

## Windows Development Notes

### Unicode/Encoding Issues
**CRITICAL**: When running Python commands on Windows, avoid Unicode characters (like ✅, 🎉, etc.) in print statements or command outputs due to Windows console encoding limitations (cp1252).

**Safe Testing Commands:**
```bash
# Test basic import (avoid Unicode in output)
uv run python -c "import src.league_analysis_mcp_server; print('Import successful')"

# Test server module directly 
uv run python -m src.league_analysis_mcp_server --help

# Run all tests
uv run python test_server.py
uv run python test_auth.py  
uv run python test_startup.py
```

**Avoid:**
```bash
# DON'T USE - causes UnicodeEncodeError on Windows
uv run python -c "print('✅ Success')"
```

## Configuration Notes
- Server runs on stdio transport (standard for MCP)
- No HTTP endpoints - purely MCP protocol communication
- OAuth tokens are stored in environment variables, not files
- Cache data is stored in memory (not persistent across restarts)