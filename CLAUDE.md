# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Think carefully and implement the most concise solution that changes as little code as possible.

## USE SUB-AGENTS FOR CONTEXT OPTIMIZATION

### 1. Always use the file-analyzer sub-agent when asked to read files.
The file-analyzer agent is an expert in extracting and summarizing critical information from files, particularly log files and verbose outputs. It provides concise, actionable summaries that preserve essential information while dramatically reducing context usage.

### 2. Always use the code-analyzer sub-agent when asked to search code, analyze code, research bugs, or trace logic flow.

The code-analyzer agent is an expert in code analysis, logic tracing, and vulnerability detection. It provides concise, actionable summaries that preserve essential information while dramatically reducing context usage.

### 3. Always use the test-runner sub-agent to run tests and analyze the test results.

Using the test-runner agent ensures:

- Full test output is captured for debugging
- Main conversation stays clean and focused
- Context usage is optimized
- All issues are properly surfaced
- No approval dialogs interrupt the workflow

### 4. Use parallel execution for independent tasks.

**For independent tasks (like fixing errors in different files):**
- Use **multiple Task tool calls in a single message** to launch agents simultaneously
- Use **Jujutsu working copies** (`jj new -m "description"`) for true isolation
- Each agent works in its own commit/working copy with zero conflicts

**For complex coordinated work:**
- Use the **parallel-worker sub-agent** for git worktree coordination
- It manages dependencies and consolidates results across work streams

## Philosophy

### Error Handling

- **Fail fast** for critical configuration (missing text model)
- **Log and continue** for optional features (extraction model)
- **Graceful degradation** when external services unavailable
- **User-friendly messages** through resilience layer

### Testing

- Always use the test-runner agent to execute tests.
- Do not use mock services for anything ever.
- Do not move on to the next test until the current test is complete.
- If the test fails, consider checking if the test is structured correctly before deciding we need to refactor the codebase.
- Tests to be verbose so we can use them for debugging.

## Tone and Behavior

- Criticism is welcome. Please tell me when I am wrong or mistaken, or even when you think I might be wrong or mistaken.
- Please tell me if there is a better approach than the one I am taking.
- Please tell me if there is a relevant standard or convention that I appear to be unaware of.
- Be skeptical.
- Be concise.
- Short summaries are OK, but don't give an extended breakdown unless we are working through the details of a plan.
- Do not flatter, and do not give compliments unless I am specifically asking for your judgement.
- Occasional pleasantries are fine.
- Feel free to ask many questions. If you are in doubt of my intent, don't guess. Ask.

## ABSOLUTE RULES:

- NO PARTIAL IMPLEMENTATION
- NO SIMPLIFICATION : no "//This is simplified stuff for now, complete implementation would blablabla"
- NO CODE DUPLICATION : check existing codebase to reuse functions and constants Read files before writing new functions. Use common sense function name to find them easily.
- NO DEAD CODE : either use or delete from codebase completely
- IMPLEMENT TEST FOR EVERY FUNCTIONS
- NO CHEATER TESTS : test must be accurate, reflect real usage and be designed to reveal flaws. No useless tests! Design tests to be verbose so we can use them for debuging.
- NO INCONSISTENT NAMING - read existing codebase naming patterns.
- NO OVER-ENGINEERING - Don't add unnecessary abstractions, factory patterns, or middleware when simple functions would work. Don't think "enterprise" when you need "working"
- NO MIXED CONCERNS - Don't put validation logic inside API handlers, database queries inside UI components, etc. instead of proper separation
- NO RESOURCE LEAKS - Don't forget to close database connections, clear timeouts, remove event listeners, or clean up file handles

## Development Commands

### Essential Commands
```bash
# Install dependencies and build
uv sync --all-extras

# Type checking (both tools available)
uv run pyright src/        # Fast type checking with good inference
uv run mypy .             # Strict type checking for CI

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

### Parallel Development Workflow

#### Initial Setup
```bash
# Initialize jujutsu for parallel work (one-time setup)
jj git init --colocate
jj bookmark track main@origin

# Verify setup
jj status  # Check current working copy status
jj log --oneline -n 5  # View recent commits
```

#### Creating Parallel Working Copies
```bash
# Sync with remote before creating working copies
jj git fetch
jj rebase -d main@origin

# Create multiple isolated working copies for parallel fixes
jj new -m "fix-pyright-test-tools: Fix pyright errors in test_tools.py"
jj new -m "fix-pyright-test-cache: Fix pyright errors in test_cache.py"
jj new -m "fix-pyright-test-auth: Fix pyright errors in test_auth.py"
jj new -m "implement-tools-impl: Create tools_impl.py architecture"
jj new -m "update-documentation: Update context files"

# Verify parallel working copies created
jj log --oneline -r 'heads()'  # Show all working copy heads
```

#### Working in Parallel Copies
```bash
# Navigate between working copies
jj edit <commit-id>  # Switch to specific working copy
jj edit @-  # Switch to parent commit

# Check current working copy context
jj status  # Current working copy status
jj show  # Show current working copy changes
jj diff  # Show working copy changes in detail

# Monitor parallel development progress
jj log --graph --color=always | head -20  # Visual progress graph
```

#### Consolidating Parallel Work (Conflict-Free)
```bash
# Individual working copy rebase to main (safest method)
jj rebase -r <commit> -d main  # Rebase single working copy
jj rebase -r <commit1> -d main  # Rebase another working copy
jj rebase -r <commit2> -d main  # Continue for each working copy

# Multi-commit rebase (for related changes)
jj rebase -s <commit1> -s <commit2> -d main  # Rebase multiple commits together

# Verify consolidation
jj log --oneline -n 10  # Check final commit structure
jj status  # Ensure clean working state
```

#### Cleanup and Finalization
```bash
# Clean up empty or obsolete working copies
jj abandon <commit>  # Remove empty/obsolete working copies

# Push consolidated changes
jj git push  # Push through Git to origin

# Verification commands
git status  # Verify Git state consistency
git log --oneline -5  # Check Git commit history
```

#### Parallel Agent Integration
```bash
# Use with Claude Code parallel agents via multiple Task tool calls
# Each Task agent automatically creates isolated working copy:
# Task 1: jj new -m "agent-1: Fix pyright errors in test_tools.py"
# Task 2: jj new -m "agent-2: Fix pyright errors in test_cache.py"
# Task 3: jj new -m "agent-3: Implement testable architecture"

# Monitor agent progress
jj log --graph  # Visualize parallel agent development
jj log --oneline -r 'heads()'  # Show all active agent working copies

# After agent completion, consolidate manually
jj rebase -r <agent-1-commit> -d main
jj rebase -r <agent-2-commit> -d main
jj rebase -r <agent-3-commit> -d main
```

### Jujutsu Best Practices

#### Daily Development Workflow
```bash
# Start of day - sync with remote
jj git fetch
jj log --oneline -n 5  # Check recent changes
jj rebase -d main@origin  # Rebase current work on latest main

# Create new working copy for focused work
jj new -m "descriptive-name: What this working copy accomplishes"

# Regular development cycle
jj commit -m "Progress: Incremental changes"  # Commit frequently
jj show  # Review current changes
jj diff  # Detailed change review

# Before consolidating - clean up working copy
jj squash  # Combine related commits if needed
jj describe -m "Final clean description"  # Update commit message
```

#### Working Copy Management
```bash
# List all working copies and their status
jj log --oneline -r 'heads()'  # All working copy heads
jj log --graph -r 'heads()::' | head -20  # Visual working copy graph

# Navigate working copies efficiently
jj edit <commit-id>  # Switch to specific working copy
jj prev  # Move to parent commit
jj next  # Move to child commit (if exists)

# Working copy information
jj status  # Current working copy detailed status
jj show @  # Show current working copy changes
jj log --oneline @ -A 3 -B 3  # Context around current working copy
```

#### Conflict-Free Parallel Development
```bash
# Pattern A: Independent parallel tasks (our breakthrough pattern)
jj new -m "task-1: Fix type errors in module A"
jj new -m "task-2: Fix type errors in module B" 
jj new -m "task-3: Implement new architecture"

# Each task works in isolation - zero conflicts
# Consolidation is always clean via jj rebase -r

# Pattern B: Coordinate dependent tasks
jj new -m "foundation: Implement base functionality"
# Complete foundation work first
jj new -m "dependent: Build on foundation" 
jj rebase -r @ -d <foundation-commit>  # Make dependent follow foundation
```

#### Error Recovery and Troubleshooting
```bash
# Undo last operation (safest recovery method)
jj undo  # Reverses the most recent jj operation
jj undo --what next  # Preview what would be undone

# Examine operation history
jj operation log  # View all jj operations
jj operation log --limit 10  # Recent operations only

# Working copy stuck or confused
jj abandon @  # Abandon current working copy
jj edit main  # Return to main branch clean state
jj new -m "restart: Clean working copy"  # Start fresh

# Find specific commits
jj log --oneline -r 'description(fix-auth)'  # Search by commit message
jj log --oneline -r 'author("your-name")'  # Search by author
```

#### Integration with Git Workflows
```bash
# Maintain Git compatibility
jj git fetch  # Sync with Git remotes regularly
jj bookmark list  # Check tracked bookmarks
jj bookmark track main@origin  # Ensure main is tracked

# Before pushing to Git
jj log --oneline main@origin..@  # See commits to be pushed
jj rebase -d main@origin  # Ensure up-to-date with remote
jj git push  # Push through Git

# Verify Git state after Jujutsu operations
git status  # Should show clean working directory
git log --oneline -5  # Verify Git sees same commits
git branch  # Should be on appropriate branch
```

#### Troubleshooting Common Issues

**Detached HEAD in Git after Jujutsu work:**
```bash
# Normal behavior - Jujutsu uses working copies, not Git branches
git checkout main  # Return to Git main branch
git merge <commit-hash>  # Merge Jujutsu work if needed
# OR better: use jj git push to push through Jujutsu
```

**Working copy conflicts:**
```bash
# Jujutsu handles most conflicts automatically
jj status  # Check for conflict markers
jj resolve  # Interactive conflict resolution if needed
jj rebase --continue  # Continue after resolving
```

**Lost working copy:**
```bash
jj log --oneline -r 'heads()'  # Find all working copy heads
jj operation log  # Review recent operations
jj edit <commit-id>  # Return to specific working copy
```

#### Performance and Maintenance
```bash
# Keep repository clean
jj abandon <empty-commit>  # Remove empty working copies
jj operation gc  # Clean up operation log (if available)

# Monitor repository health
jj log --oneline | head -20  # Recent commit overview
jj bookmark list  # Check bookmark status
jj git fetch --dry-run  # Check remote without fetching
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

## Reference: Breakthrough Parallel Development Pattern

This section documents our proven parallel development breakthrough that fixed 74 pyright errors across 6 test files simultaneously using Jujutsu working copies and parallel Claude Code agents.

### The 74 Pyright Error Fix Workflow (2025-09-05)

**Scope**: 6 test files with comprehensive type safety overhaul  
**Duration**: Single development session  
**Method**: Parallel agents with isolated Jujutsu working copies  
**Result**: Zero conflicts, complete success

#### Step 1: Parallel Working Copy Creation
```bash
# Initialize parallel development environment
jj git init --colocate
jj bookmark track main@origin

# Create isolated working copies for each parallel task
jj new -m "fix-test-tools-pyright: Fix pyright errors in test_tools.py"
jj new -m "fix-test-cache-pyright: Fix pyright errors in test_cache.py"
jj new -m "fix-test-auth-pyright: Fix pyright errors in test_auth.py"
jj new -m "fix-functional-pyright: Fix pyright errors in functional tests"
jj new -m "fix-workflows-pyright: Fix pyright errors in test_workflows.py"
jj new -m "implement-testable-arch: Create tools_impl.py separation"

# Verify parallel isolation
jj log --oneline -r 'heads()'  # Should show 6 working copy heads
```

#### Step 2: Parallel Agent Execution
**Claude Code Implementation**:
- **Multiple Task tool calls in single message** for true parallelism
- **Each agent automatically creates isolated working copy**
- **Zero inter-agent conflicts** due to working copy isolation
- **Simultaneous execution** of type error fixes across different files

**Agent Task Distribution**:
- Agent 1: `test_tools.py` - 15 pyright errors
- Agent 2: `test_cache.py` - 12 pyright errors  
- Agent 3: `test_auth.py` - 18 pyright errors
- Agent 4: `functional tests` - 14 pyright errors
- Agent 5: `test_workflows.py` - 11 pyright errors
- Agent 6: `tools_impl.py` - Architectural pattern implementation (4 errors)

#### Step 3: Conflict-Free Consolidation
```bash
# Each agent completed in isolated working copy
# Manual consolidation with zero conflicts
jj rebase -r <fix-test-tools-commit> -d main
jj rebase -r <fix-test-cache-commit> -d main
jj rebase -r <fix-test-auth-commit> -d main
jj rebase -r <fix-functional-commit> -d main
jj rebase -r <fix-workflows-commit> -d main
jj rebase -r <implement-arch-commit> -d main

# Final integration
git merge <final-commit-hash>  # Merge consolidated work
git push origin main  # Publish breakthrough
```

#### Architectural Innovations Implemented

**Testable Architecture Pattern**:
```python
# tools_impl.py - Private implementation functions
def get_league_info_impl(league_id: str, sport: str, season: Optional[str], app_state: Dict) -> Dict:
    """Private implementation - testable without MCP decorators."""
    # Core business logic here

# tools.py - Public API + MCP wrappers  
@mcp.tool()
def get_league_info(league_id: str, sport: str = "nfl", season: Optional[str] = None) -> Dict:
    """MCP tool wrapper - delegates to implementation."""
    return get_league_info_impl(league_id, sport, season, app_state)

# Public API for testing
def get_league_info(league_id: str, sport: str = "nfl", season: Optional[str] = None) -> Dict:
    """Public API function for testing and direct access."""
    return get_league_info_impl(league_id, sport, season, app_state)
```

### Key Success Factors

1. **Working Copy Isolation** - Each agent worked without any awareness of other agents
2. **Jujutsu Safety** - `jj undo` available for any mistakes, non-destructive operations
3. **Parallel Task Design** - Each task focused on single file/module to eliminate dependencies  
4. **Systematic Approach** - Consistent type error resolution patterns across all files
5. **Architectural Separation** - tools_impl.py pattern enabled better testability

### Breakthrough Metrics

- **Files Modified**: 9 total (6 test files + 3 supporting files)
- **Pyright Errors Fixed**: 74 across entire codebase
- **Working Copies**: 6 simultaneous isolated environments
- **Conflicts**: 0 (complete conflict-free development)
- **Development Time**: Single session with parallel execution
- **Success Rate**: 100% - all agents completed successfully

### Replication Guide

To replicate this breakthrough pattern for other parallel development tasks:

1. **Task Identification** - Identify independent, parallelizable tasks
2. **Working Copy Creation** - `jj new -m "descriptive-task-name"` for each task  
3. **Parallel Execution** - Multiple Task tool calls in single Claude Code message
4. **Isolation Verification** - `jj log -r 'heads()'` to confirm parallel work
5. **Systematic Consolidation** - `jj rebase -r <commit> -d main` for each working copy
6. **Integration Testing** - Verify consolidated result works correctly

This pattern is now proven and documented for future parallel development work requiring conflict-free simultaneous execution across multiple files or modules.