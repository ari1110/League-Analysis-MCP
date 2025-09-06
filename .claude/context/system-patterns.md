---
created: 2025-09-04T19:09:18Z
last_updated: 2025-09-05T20:43:03Z
version: 1.4
author: Claude Code PM System
---

# System Patterns & Architecture

## Core Architectural Patterns

### 1. Model Context Protocol (MCP) Server Pattern
- **Protocol**: Standard MCP 1.0 over stdio transport
- **Tool Registration**: Decorator-based tool exposure (`@mcp.tool()`)
- **Resource Endpoints**: URI-based read-only data access (`@mcp.resource()`)
- **State Management**: Global app state with dependency injection
- **Communication**: JSON-RPC 2.0 message format

### 2. Manager Pattern for Stateful Components
**Authentication Manager** (`enhanced_auth.py`):
- Centralized OAuth token management
- Automatic token refresh handling  
- Environment variable-based credential storage
- Conversation-driven setup workflow

**Cache Manager** (`cache.py`):
- TTL-based cache with size limits
- Differentiated caching strategy (permanent vs. temporary)
- LRU eviction policy
- Thread-safe operations

### 3. Tool Categorization Pattern
**Domain-Specific Tool Modules**:
- `tools.py` - Basic league operations (MCP tool wrappers only)
- `tools_impl.py` - Implementation functions for testable architecture
- `historical.py` - Multi-season analysis
- `analytics.py` - Advanced pattern recognition (trade analysis bug fixed)
- `game_tools.py` - Game and season management
- `team_tools.py` - Team-specific operations
- `player_tools.py` - Player statistics and ownership
- `utility_tools.py` - Maintenance, troubleshooting, and user account access (consolidated)

**Testable Architecture Pattern**:
- **Private Implementation Functions**: `_impl` suffix for business logic
- **Public API Functions**: Clean interfaces for external consumption
- **MCP Tool Wrappers**: Minimal decorators that delegate to implementation

### 4. Resource Pattern for Read-Only Data
**URI-Based Resource Access**:
```python
# Resource URI patterns
league_overview://sport/league_id[/season]
current_week://sport/league_id  
league_history://sport/league_id
manager_profiles://sport/league_id[/team_id]
```

## Data Flow Patterns

### 1. Request-Response Pipeline
```python
MCP Client Request
  → FastMCP Framework
  → Authentication Verification (enhanced_auth.py)
  → Cache Lookup (cache.py)
  → Yahoo API Call (if cache miss)
  → Data Transformation (Pydantic models)
  → Analytics Processing (if applicable)
  → Cache Storage
  → Response Formatting
  → MCP Client Response
```

### 2. Authentication Flow Pattern (Streamlined v0.3.0+)
**Conversational OAuth Setup**:
```python
check_setup_status()
  → Determine required steps
  → Guide user through Yahoo Developer app creation
save_yahoo_credentials()
  → Store consumer key/secret in environment
start_automated_oauth_flow()
  → Handle OAuth authorization automatically
  → Exchange code for tokens
  → Store tokens securely
# Legacy manual/testing methods removed for simplicity
```

### 3. Caching Strategy Pattern
**Differentiated TTL Strategy**:
- **Historical Data**: TTL = -1 (permanent cache)
  - Draft results from previous seasons
  - Final standings and championship data
  - Completed transaction history
- **Current Season Data**: TTL = 300 (5 minutes)
  - Live standings and scores
  - Active rosters and lineups
  - Current week matchups
  - Recent transactions

### 4. Error Handling Pattern
**Graceful Degradation**:
```python
try:
    # Primary operation (API call)
    result = await yahoo_api_call()
except AuthenticationError:
    # Guide user through re-authentication
    return authentication_guidance()
except RateLimitError:
    # Check cache for fallback data
    return cached_fallback_or_retry_guidance()
except NetworkError:
    # Provide cached data if available
    return cache_fallback_or_error_message()
```

## Design Patterns Implementation

### 1. Dependency Injection Pattern
**Global App State Container**:
```python
# server.py - Global app state
app_state = {
    'auth_manager': EnhancedAuthManager(),
    'cache_manager': CacheManager(), 
    'config': load_config(),
    'game_ids': load_game_ids()
}
```

### 2. Factory Pattern for Data Models
**Pydantic Model Factories**:
- Standardized data validation across all API responses
- Type-safe data transformation
- Automatic JSON serialization/deserialization
- Configuration validation

### 3. Strategy Pattern for Analytics
**Manager Profiling Strategies**:
- **Performance Tier Calculation**: Multiple metric aggregation
- **Draft Strategy Classification**: Pattern recognition algorithms
- **Trade Likelihood Prediction**: Historical pattern analysis
- **Skill Evaluation**: Composite scoring methodologies

### 4. Observer Pattern for Cache Management
**Cache Event Handling**:
- Size limit enforcement
- TTL expiration monitoring
- Memory usage tracking
- Eviction policy execution

## Integration Patterns

### 1. External API Integration Pattern
**Yahoo Fantasy Sports API**:
```python
# Standardized API call pattern
async def get_yahoo_data(endpoint, params):
    # Check authentication
    await auth_manager.ensure_valid_token()
    
    # Check cache first
    cache_key = generate_cache_key(endpoint, params)
    cached_result = cache_manager.get(cache_key)
    if cached_result:
        return cached_result
    
    # Rate limiting
    await rate_limiter.acquire()
    
    # API call with error handling
    try:
        result = await yahoo_api.call(endpoint, params)
        # Cache result with appropriate TTL
        cache_manager.set(cache_key, result, ttl=get_ttl_for_data_type(endpoint))
        return result
    except Exception as e:
        # Graceful error handling
        return handle_api_error(e, endpoint, params)
```

### 2. MCP Client Integration Pattern
**Multi-Client Support**:
- **Claude Desktop**: JSON configuration with uvx command
- **Claude Code**: Direct MCP protocol integration
- **Continue.dev**: Extension-based MCP server connection
- **Custom Clients**: Standard MCP 1.0 protocol compatibility

### 3. Authentication Integration Pattern (Streamlined v0.3.0+)
**OAuth 2.0 with Automated Flow**:
- **Automated Flow**: HTTPS callback server captures authorization code (recommended)
- **Token Management**: Automatic refresh with fallback to re-authentication
- **Simplified UX**: Single OAuth method eliminates user confusion

## Performance Patterns

### 1. Caching Performance Pattern
**Multi-Level Caching Strategy**:
```python
# Level 1: Method-level caching for expensive computations
@lru_cache(maxsize=128)
def calculate_manager_skill_score(stats):
    return complex_calculation(stats)

# Level 2: Data-level caching for API responses  
cache_manager.set(api_key, response, ttl=300)

# Level 3: Permanent caching for historical data
cache_manager.set(historical_key, data, ttl=-1)
```

### 2. Rate Limiting Pattern
**Respect API Limits**:
- **Yahoo API**: 60 requests per minute maximum
- **Implementation**: asyncio-throttle with burst handling
- **Strategy**: Aggressive caching to minimize API calls
- **Monitoring**: Track request rates and adjust behavior

### 3. Batch Processing Pattern
**Historical Data Analysis**:
```python
# Process multiple seasons efficiently
async def analyze_historical_drafts(league_id, seasons):
    # Batch API calls with rate limiting
    draft_data = []
    for season in seasons:
        # Check cache first (likely hit for historical data)
        cached = cache_manager.get(f"draft_{league_id}_{season}")
        if cached:
            draft_data.append(cached)
        else:
            # Rate-limited API call
            await rate_limiter.acquire()
            data = await fetch_draft_data(league_id, season)
            cache_manager.set(f"draft_{league_id}_{season}", data, ttl=-1)
            draft_data.append(data)
    
    # Process all data together
    return analyze_draft_patterns(draft_data)
```

## Scalability Patterns

### 1. Memory Management Pattern
**Bounded Cache with Eviction**:
- **Size Limit**: 100MB default (configurable)
- **Eviction Policy**: LRU (Least Recently Used)
- **Monitoring**: Memory usage tracking and alerts
- **Optimization**: Prefer historical data retention over current data

### 2. Async Processing Pattern
**Non-Blocking Operations**:
- **AsyncIO**: All I/O operations are asynchronous
- **Concurrency**: Multiple requests processed concurrently
- **Rate Limiting**: Coordinated across concurrent requests
- **Resource Management**: Connection pooling and cleanup

### 3. Modular Extension Pattern
**Domain-Specific Tool Modules**:
- **Separation of Concerns**: Each module handles specific entity types
- **Independent Development**: Modules can be developed and tested separately
- **Extensibility**: New modules can be added without modifying existing code
- **Maintainability**: Clear boundaries and responsibilities

## Security Patterns

### 1. Credential Management Pattern
**Environment Variable Storage**:
- **OAuth Tokens**: Stored in environment variables (not files)
- **Consumer Keys**: Separate from source code and version control
- **Token Rotation**: Automatic refresh with secure storage
- **Access Control**: Limited to necessary OAuth scopes

### 2. Input Validation Pattern
**Pydantic Model Validation**:
- **Type Safety**: All inputs validated through Pydantic models
- **Sanitization**: Automatic data cleaning and transformation
- **Error Handling**: Clear validation error messages
- **Security**: Prevents injection attacks through type enforcement

### 3. Error Information Security Pattern
**Safe Error Reporting**:
- **Sensitive Data**: Never expose OAuth tokens or keys in error messages
- **User-Friendly Messages**: Convert technical errors to user-actionable guidance
- **Logging Strategy**: Detailed logs for debugging, sanitized responses for users
- **Attack Surface**: Minimize information disclosure in error responses

## Testing Patterns

### 1. Test Independence Pattern
**Isolated Test Execution**:
- **No External Dependencies**: Tests run without Yahoo API credentials
- **Mock Integration**: Core functionality tested with mocked dependencies
- **Fast Execution**: All tests complete in under 10 seconds
- **Reproducible Results**: Tests produce consistent results across environments

### 2. Component Testing Pattern
**Modular Test Structure**:
- `test_server.py` - Server initialization and import validation
- `test_auth.py` - Authentication system without external calls
- `test_startup.py` - Configuration loading and validation
- `test_mcp_connection.py` - MCP protocol communication
- `test_comprehensive.py` - Static analysis and comprehensive coverage

### 3. Streamlined Testing Pattern (v0.3.0+)
**Core Structural Testing**:
- **Focused Testing Approach**: Dropped complex functional test framework in favor of reliable structural tests
- **Import Validation**: Comprehensive module import and initialization testing
- **Authentication Testing**: OAuth system validation without external dependencies
- **Configuration Testing**: Settings loading and validation testing
- **Performance**: All structural tests complete under 10 seconds

**Structural Test Architecture**:
- `test_server.py` - Server initialization and MCP protocol setup
- `test_auth.py` - Authentication system without external Yahoo API calls
- `test_startup.py` - Configuration loading and application startup
- `test_mcp_connection.py` - MCP protocol communication validation

### 4. Static Analysis Integration Pattern
**Quality Assurance Automation**:
- **Ruff Integration**: Automated code quality and linting checks
- **MyPy Integration**: Static type checking with error reporting
- **IDE Diagnostics**: Real-time analysis via MCP getDiagnostics tool
- **Comprehensive Coverage**: Function-level testing and error handling validation
- **Windows Compatibility**: Unicode-safe output for cross-platform support
- `test_comprehensive.py` - Static analysis and comprehensive coverage

## Development Workflow Patterns

### 1. Enhanced Documentation Pattern (v0.3.0+)
**Comprehensive Workflow Documentation**:
- **Command Verification**: All workflow commands verified against actual tool versions (Jujutsu v0.33.0)
- **Layered Documentation**: Basic commands → advanced workflows → best practices → troubleshooting
- **Reference Patterns**: Document proven breakthrough patterns as replicable templates
- **Agent Integration**: Document sub-agent coordination with parallel development workflows

**Documentation Structure**:
- **CLAUDE.md**: 30+ verified Jujutsu commands with complete parallel development workflows
- **Agent Configurations**: Enhanced parallel-worker.md and repo-issue-fixer.md with working copy support
- **Best Practices**: Daily workflows, error recovery, performance optimization, and maintenance
- **Safety Guidelines**: Detailed safety comparisons (jj rebase vs git rebase, recovery methods)

## Code Organization Patterns

### 1. Shared Utilities Pattern (v0.3.0+)
**Centralized Common Functionality**:
- **shared_utils.py**: Single source of truth for common functions across modules
- **Eliminated Duplication**: Removed 140+ lines of duplicate `get_yahoo_query()` implementations
- **Standardized Error Handling**: Consistent `handle_api_error()` patterns across all modules
- **Cache Key Generation**: Centralized `standardize_cache_key()` function

**Implementation Pattern**:
```python
# shared_utils.py - Centralized utilities
def get_yahoo_query(league_id: str, app_state: Dict, game_id: Optional[str] = None, sport: str = "nfl")
def handle_api_error(operation: str, error: Exception) -> Dict[str, Any]
def standardize_cache_key(category: str, identifiers: Dict[str, Any], season: Optional[str] = None)

# tool modules - Import and use shared functions
from .shared_utils import get_yahoo_query, handle_api_error
```

**Benefits**:
- **Single Source of Truth**: Changes to common logic only need to be made in one place
- **Consistent Behavior**: All modules use identical error handling and API query logic
- **Reduced Maintenance**: No more duplicate code to keep in sync across 5+ modules