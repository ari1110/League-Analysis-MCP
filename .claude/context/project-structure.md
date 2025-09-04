---
created: 2025-09-04T19:09:18Z
last_updated: 2025-09-04T22:09:53Z
version: 1.2
author: Claude Code PM System
---

# Project Structure

## Directory Organization

### Root Level Structure
```
League-Analysis-MCP/
├── .claude/                 # Claude Code configuration and project management
├── .github/                 # GitHub Actions workflows and repository templates  
├── config/                  # Server configuration files
├── src/                     # Source code (Python package)
├── tests/                   # Test suite
├── utils/                   # Utility scripts and tools
├── example_configs/         # Example MCP client configurations
├── CLAUDE.md               # Main project instructions and development guidelines
├── README.md               # Primary documentation
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Dependency lock file
└── .env                    # Environment variables (OAuth tokens, etc.)
```

### Source Code Structure (`src/league_analysis_mcp_server/`)
```
src/league_analysis_mcp_server/
├── __init__.py             # Package initialization
├── __main__.py             # Entry point for CLI execution
├── server.py               # FastMCP server initialization and app state
├── enhanced_auth.py        # Enhanced authentication manager with OAuth
├── oauth_callback_server.py # HTTPS callback server for automated OAuth
├── cache.py                # Caching layer with TTL and size management
├── tools.py                # Basic MCP tools (league info, standings, rosters)
├── historical.py           # Historical analysis tools (multi-season data)
├── analytics.py            # Advanced analytics (manager profiling, predictions)
├── resources.py            # MCP resources (read-only data access)
├── game_tools.py           # Game-related MCP tools
├── team_tools.py           # Team-specific MCP tools  
├── player_tools.py         # Player-specific MCP tools
├── user_tools.py           # User account MCP tools
├── utility_tools.py        # Utility and maintenance MCP tools
└── enhancement_helpers.py   # Data enhancement utilities
```

### Configuration Structure (`config/`)
```
config/
├── settings.json           # Server metadata, cache settings, rate limiting
└── game_ids.json          # Yahoo game ID mappings (2015-2024, all sports)
```

### Test Structure (`tests/`)
```
tests/
├── test_server.py          # Server initialization and import tests
├── test_auth.py            # Authentication system tests  
├── test_startup.py         # Startup and configuration tests
├── test_mcp_connection.py  # MCP protocol connection tests
└── test_type_fixes.py      # Type safety and validation tests
```

### Claude Code Management (`.claude/`)
```
.claude/
├── settings.local.json     # Local Claude Code settings
├── CLAUDE.md              # Development rules and sub-agent optimization
├── agents/                # Sub-agent configurations
├── commands/              # Custom Claude Code commands  
├── context/               # Project context documentation (this file)
├── epics/                 # Epic definitions and tracking
├── prds/                  # Product requirements documents
├── rules/                 # Development rules and standards
└── scripts/               # Automation and utility scripts
```

## File Naming Patterns

### Python Modules
- **Snake case**: `enhanced_auth.py`, `oauth_callback_server.py`
- **Descriptive names**: Files clearly indicate their primary responsibility
- **Logical grouping**: Related functionality grouped by domain (auth, cache, tools)

### Configuration Files
- **JSON format**: `settings.json`, `game_ids.json`
- **Descriptive names**: Purpose immediately clear from filename
- **Versioned**: Both config files maintain synchronized version numbers

### Documentation Files
- **UPPERCASE**: `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `RELEASE.md`
- **Underscores for context**: `MCP_INTEGRATION_GUIDE.md`
- **Clear purpose**: Filename indicates content and audience

### Test Files
- **Prefix pattern**: `test_*.py`
- **Comprehensive testing**: `test_comprehensive.py` with static analysis integration
- **Domain-specific**: `test_auth.py`, `test_server.py`, `test_startup.py`, `test_mcp_connection.py`
- **Domain-specific**: Each test file focuses on specific functionality
- **Executable permissions**: All test files are executable for direct execution

## Module Organization

### Core Server Components
1. **`server.py`** - Central FastMCP server with global app state
2. **`enhanced_auth.py`** - Primary authentication manager
3. **`cache.py`** - Caching layer with smart TTL management
4. **`resources.py`** - Read-only MCP resource endpoints

### Tool Categories (MCP Tools)
1. **Basic Tools** (`tools.py`) - Essential league operations
2. **Historical Tools** (`historical.py`) - Multi-season analysis
3. **Analytics Tools** (`analytics.py`) - Advanced pattern recognition
4. **Domain-Specific Tools** - Specialized tools by entity type:
   - `game_tools.py` - Game and season operations
   - `team_tools.py` - Team management and analysis
   - `player_tools.py` - Player statistics and ownership
   - `user_tools.py` - User account and league access
   - `utility_tools.py` - Maintenance and troubleshooting

### Authentication Architecture
1. **Enhanced Auth Manager** - Primary OAuth handler with token management
2. **OAuth Callback Server** - HTTPS server for automated code capture
3. **Token Storage** - Environment variable-based credential storage
4. **Connection Testing** - Separate YFPY integration validation

## Data Flow Patterns

### Request Processing Flow
```
MCP Client Request 
    → FastMCP Server (server.py)
    → Authentication Check (enhanced_auth.py)
    → Cache Lookup (cache.py)
    → Yahoo API Call (via tools)
    → Data Processing
    → Cache Storage
    → Response to Client
```

### Authentication Flow
```
User Request 
    → check_setup_status()
    → create_yahoo_app() [if needed]
    → save_yahoo_credentials()
    → start_automated_oauth_flow() OR start_oauth_flow()
    → Token Exchange & Storage
    → test_yahoo_connection() [optional]
```

### Caching Strategy
- **Historical Data**: `cache.py` with TTL = -1 (permanent)
- **Current Season**: `cache.py` with TTL = 300 (5 minutes)
- **Size Management**: 100MB limit with smart eviction
- **Key Strategy**: Sport + League ID + Season + Data Type

## Integration Points

### External Dependencies
- **FastMCP 2.0**: Primary MCP framework integration
- **YFPY 16.0+**: Yahoo Fantasy Sports API wrapper
- **Yahoo OAuth API**: Authentication and token exchange
- **Python Standard Library**: asyncio, logging, json, datetime

### MCP Client Integration  
- **Claude Desktop**: JSON configuration with uvx command
- **Claude Code**: Direct server integration via MCP protocol
- **Continue.dev**: Extension-based MCP server connection
- **Custom Clients**: Standard MCP protocol over stdio transport

### File System Integration
- **Environment Variables**: `.env` file for OAuth tokens
- **Configuration Files**: JSON-based settings and game ID mappings
- **Cache Storage**: In-memory with optional persistence
- **Log Output**: Standard logging to stderr for MCP compatibility

## Development Conventions

### Import Organization
1. **Standard library imports** (alphabetical)
2. **Third-party imports** (alphabetical)  
3. **Local application imports** (alphabetical)
4. **Relative imports** (if any)

### Function Organization Within Files
1. **Constants and configuration**
2. **Helper functions**
3. **Main functionality**
4. **MCP tool decorators** (for tool files)
5. **Error handling utilities**

### Class Organization
- **Pydantic models** for data validation
- **Manager classes** for stateful operations (AuthManager, CacheManager)
- **Utility classes** for data transformation
- **Exception classes** for custom error handling