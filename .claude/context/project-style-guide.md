---
created: 2025-09-04T19:09:18Z
last_updated: 2025-09-04T19:09:18Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide & Development Standards

## Coding Philosophy

### Core Principles from .claude/CLAUDE.md

> **"Think carefully and implement the most concise solution that changes as little code as possible."**

#### Absolute Development Rules
- **NO PARTIAL IMPLEMENTATION** - Complete all functionality or don't implement
- **NO SIMPLIFICATION** - No placeholder comments or incomplete logic
- **NO CODE DUPLICATION** - Reuse existing functions and constants
- **NO DEAD CODE** - Remove unused code completely
- **NO INCONSISTENT NAMING** - Follow established patterns throughout codebase
- **NO OVER-ENGINEERING** - Prefer simple functions over complex abstractions
- **NO MIXED CONCERNS** - Clear separation between validation, API, and UI logic
- **NO RESOURCE LEAKS** - Proper cleanup of connections, timeouts, and file handles

## Python Coding Standards

### Import Organization
**Required Order** (PEP 8 compliant):
```python
# 1. Standard library imports (alphabetical)
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party imports (alphabetical)
import pandas as pd
import requests
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 3. Local application imports (alphabetical)
from .cache import CacheManager
from .enhanced_auth import EnhancedAuthManager

# 4. Relative imports (if any)
from . import utils
```

### Function and Class Naming

#### Function Naming Patterns
```python
# MCP tools: action_noun pattern
def get_league_info() -> Dict:
def analyze_draft_strategy() -> AnalysisResult:
def predict_trade_likelihood() -> PredictionResult:

# Internal helpers: descriptive_verb pattern  
def validate_league_params() -> bool:
def format_standings_data() -> List[Dict]:
def calculate_manager_score() -> float:

# Async operations: explicit async prefix when needed
async def fetch_yahoo_data() -> Dict:
async def process_historical_analysis() -> AnalysisResult:
```

#### Class Naming Conventions
```python
# Manager classes: [Purpose]Manager pattern
class EnhancedAuthManager:
class CacheManager:

# Data models: descriptive noun pattern
class LeagueSettings(BaseModel):
class ManagerProfile(BaseModel):
class DraftAnalysisResult(BaseModel):

# Exception classes: [Domain]Error pattern
class AuthenticationError(Exception):
class CacheError(Exception):
class YahooAPIError(Exception):
```

### Variable Naming Standards

#### Constants
```python
# All caps with underscores
CACHE_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB
DEFAULT_TTL_CURRENT = 300  # 5 minutes
DEFAULT_TTL_HISTORICAL = -1  # Permanent
YAHOO_RATE_LIMIT = 60  # requests per minute
```

#### Variables
```python
# Snake case for all variables
league_id = "123456"
manager_data = fetch_manager_stats()
draft_results = analyze_draft_patterns()

# Boolean variables: is_/has_/can_/should_ prefixes
is_authenticated = True
has_valid_token = check_token_validity()
can_access_data = verify_permissions()
should_refresh_cache = check_cache_staleness()
```

## File Organization Standards

### Module Structure Pattern
```python
"""
Module docstring explaining purpose and primary functions.

Example:
    Basic usage example showing key functionality.
"""

# Imports (following import order standards)
import standard_library
from third_party import modules
from .local import modules

# Constants and configuration
CONSTANT_VALUES = "defined_here"

# Type definitions and Pydantic models
class DataModel(BaseModel):
    field: str = Field(description="Field purpose")

# Helper functions (private, prefixed with _)
def _internal_helper_function():
    """Private helper with leading underscore."""
    pass

# Public API functions
def public_api_function():
    """Public function with comprehensive docstring."""
    pass

# MCP tool decorators (at end of file)
@mcp.tool()
def mcp_tool_function():
    """MCP tool with proper decorator and documentation."""
    pass
```

### Directory Organization Conventions
- **Source Code**: `src/league_analysis_mcp_server/` - All application code
- **Tests**: `tests/` - Test files with `test_` prefix
- **Configuration**: `config/` - JSON configuration files only
- **Documentation**: Root level `.md` files for user-facing docs
- **Development**: `.claude/` - Development tools and context

## Type Safety & Validation Standards

### Pydantic Model Patterns
```python
class StandardModel(BaseModel):
    """Base model following project patterns."""
    
    # Required fields first
    league_id: str = Field(description="Yahoo league identifier")
    sport: str = Field(description="Sport code (nfl, nba, mlb, nhl)")
    
    # Optional fields with defaults
    season: Optional[str] = Field(None, description="Season year (YYYY format)")
    include_inactive: bool = Field(False, description="Include inactive players")
    
    # Validation methods
    @field_validator('sport')
    @classmethod
    def validate_sport(cls, v: str) -> str:
        allowed_sports = {'nfl', 'nba', 'mlb', 'nhl'}
        if v.lower() not in allowed_sports:
            raise ValueError(f'Sport must be one of {allowed_sports}')
        return v.lower()
    
    # Configuration
    model_config = ConfigDict(
        extra='forbid',  # Reject unknown fields
        str_strip_whitespace=True,  # Auto-trim strings
        validate_assignment=True  # Validate on assignment
    )
```

### Function Type Annotations
```python
# Complete type hints for all function signatures
def analyze_manager_performance(
    league_id: str,
    seasons: List[str],
    team_id: Optional[str] = None
) -> ManagerAnalysisResult:
    """
    Analyze manager performance across multiple seasons.
    
    Args:
        league_id: Yahoo league identifier
        seasons: List of season years to analyze
        team_id: Specific team to analyze (optional)
    
    Returns:
        Comprehensive manager analysis results
        
    Raises:
        AuthenticationError: When Yahoo credentials invalid
        CacheError: When cache operations fail
    """
    pass
```

## Error Handling Patterns

### Exception Hierarchy
```python
# Base exception for all project-specific errors
class LeagueAnalysisError(Exception):
    """Base exception for League Analysis MCP Server."""
    pass

# Specific domain exceptions
class AuthenticationError(LeagueAnalysisError):
    """Authentication and OAuth-related errors."""
    pass

class YahooAPIError(LeagueAnalysisError):
    """Yahoo Fantasy Sports API errors."""
    pass

class CacheError(LeagueAnalysisError):
    """Cache management and storage errors."""
    pass
```

### Error Handling Standard Pattern
```python
def standard_operation() -> ResultType:
    """Standard error handling pattern for all operations."""
    try:
        # Primary operation
        result = perform_operation()
        return result
        
    except AuthenticationError as e:
        # Provide user guidance for authentication issues
        logger.error(f"Authentication failed: {e}")
        raise AuthenticationError(
            "Please run check_setup_status() to verify your authentication setup"
        )
        
    except YahooAPIError as e:
        # Handle API-specific errors with fallback
        logger.warning(f"Yahoo API error: {e}")
        cached_result = try_cache_fallback()
        if cached_result:
            return cached_result
        raise YahooAPIError(f"Yahoo API unavailable: {e}")
        
    except Exception as e:
        # Catch-all with sanitized error message
        logger.error(f"Unexpected error in {operation.__name__}: {e}")
        raise LeagueAnalysisError(f"Operation failed: {type(e).__name__}")
```

## Documentation Standards

### Function Docstring Template
```python
def function_name(param1: str, param2: Optional[int] = None) -> ResultType:
    """
    Brief description of function purpose (one line).
    
    Extended description if needed, explaining behavior, side effects,
    or important implementation details.
    
    Args:
        param1: Description of first parameter
        param2: Description of optional parameter with default behavior
    
    Returns:
        Description of return value and its structure
        
    Raises:
        SpecificError: When specific condition occurs
        GeneralError: When general failure happens
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result.status)
        'success'
    """
    pass
```

### MCP Tool Documentation Pattern
```python
@mcp.tool()
def get_league_standings(
    league_id: str,
    sport: str = "nfl",
    season: Optional[str] = None
) -> Dict:
    """
    Get current or historical league standings.
    
    Retrieves win-loss records, points for/against, and playoff positioning
    for all teams in the specified league and season.
    
    Args:
        league_id: Yahoo league identifier
        sport: Sport code (nfl, nba, mlb, nhl)
        season: Season year (defaults to current season)
    
    Returns:
        Dictionary containing standings data with team records,
        points, and playoff implications
    """
    pass
```

## Performance & Caching Patterns

### Caching Implementation Standards
```python
def cached_operation(cache_key: str, operation_func, ttl: int = 300) -> Any:
    """Standard caching pattern for all operations."""
    
    # Check cache first
    cached_result = cache_manager.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for key: {cache_key}")
        return cached_result
    
    # Perform operation
    logger.debug(f"Cache miss for key: {cache_key}, executing operation")
    result = operation_func()
    
    # Store in cache
    cache_manager.set(cache_key, result, ttl=ttl)
    logger.debug(f"Cached result for key: {cache_key} with TTL: {ttl}")
    
    return result
```

### Rate Limiting Pattern
```python
async def rate_limited_api_call(endpoint: str, params: Dict) -> Dict:
    """Standard pattern for Yahoo API calls with rate limiting."""
    
    # Ensure authentication
    await auth_manager.ensure_valid_token()
    
    # Apply rate limiting
    await rate_limiter.acquire()
    
    # Make API call with error handling
    try:
        response = await yahoo_api.call(endpoint, params)
        return response
    except Exception as e:
        logger.error(f"API call failed for {endpoint}: {e}")
        raise YahooAPIError(f"Failed to fetch {endpoint}: {e}")
```

## Testing Standards

### Test File Organization
```python
"""
test_[module_name].py - Test file following module being tested.

Tests should be independent, fast, and comprehensive without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch

from league_analysis_mcp_server.module import function_to_test

class TestModuleFunction:
    """Test class for specific function or feature area."""
    
    def test_function_success_case(self):
        """Test the happy path scenario."""
        # Arrange
        test_input = "valid_input"
        expected_output = "expected_result"
        
        # Act
        result = function_to_test(test_input)
        
        # Assert
        assert result == expected_output
    
    def test_function_error_case(self):
        """Test error handling behavior."""
        # Arrange
        invalid_input = "invalid_input"
        
        # Act & Assert
        with pytest.raises(SpecificError):
            function_to_test(invalid_input)
    
    @patch('module.external_dependency')
    def test_function_with_mocked_dependency(self, mock_dependency):
        """Test with mocked external dependencies."""
        # Arrange
        mock_dependency.return_value = "mocked_response"
        
        # Act
        result = function_to_test()
        
        # Assert
        assert result is not None
        mock_dependency.assert_called_once()
```

### Test Quality Requirements
- **No External Dependencies**: Tests must run without Yahoo API credentials or internet access
- **Fast Execution**: All tests complete in <10 seconds
- **Comprehensive Coverage**: Cover success cases, error cases, and edge cases  
- **Verbose Output**: Tests provide detailed output for debugging when they fail
- **Independent**: Each test can run in isolation without dependency on other tests

## Configuration & Environment Standards

### Environment Variable Conventions
```python
# Authentication credentials (stored in .env)
YAHOO_CONSUMER_KEY="your_consumer_key_here"
YAHOO_CONSUMER_SECRET="your_consumer_secret_here"

# OAuth tokens (managed automatically)
YAHOO_ACCESS_TOKEN="auto_generated_token"
YAHOO_REFRESH_TOKEN="auto_generated_refresh_token"
YAHOO_TOKEN_EXPIRES_AT="2024-12-31T23:59:59Z"

# Optional configuration overrides
LEAGUE_ANALYSIS_CACHE_SIZE="104857600"  # 100MB in bytes
LEAGUE_ANALYSIS_LOG_LEVEL="INFO"
LEAGUE_ANALYSIS_RATE_LIMIT="60"  # requests per minute
```

### Configuration File Standards
```json
{
    "name": "league-analysis-mcp-server",
    "version": "0.2.2",
    "description": "Descriptive text about configuration purpose",
    "cache": {
        "size_limit": 104857600,
        "ttl_historical": -1,
        "ttl_current": 300
    },
    "rate_limiting": {
        "requests_per_minute": 60,
        "burst_limit": 10
    }
}
```

## Version Management Standards

### Version Synchronization Requirements
- **pyproject.toml** and **config/settings.json** versions must always match
- Use **bump_version.py** script for all version changes
- Follow **semantic versioning** (MAJOR.MINOR.PATCH)
- **Git tags** must match version numbers exactly

### Commit Message Standards
```
type: Brief description of change (max 50 chars)

Detailed explanation of what was changed and why, if needed.
Include any breaking changes or migration notes.

Examples:
feat: Add manager skill evaluation analytics
fix: Resolve OAuth token refresh race condition  
chore: Bump version to 0.2.3
docs: Update authentication setup guide
```

## Development Workflow Standards

### Code Quality Checklist
- [ ] All functions have complete type hints
- [ ] All public functions have comprehensive docstrings  
- [ ] Error handling follows project patterns
- [ ] No code duplication - reuse existing functions
- [ ] Tests cover success and error cases
- [ ] Logging provides appropriate debug information
- [ ] Configuration uses established patterns
- [ ] Performance patterns followed (caching, rate limiting)

### Pre-Commit Requirements
- **Flake8**: Code style compliance
- **MyPy**: Type checking validation
- **Tests**: All tests pass
- **Version Check**: Ensure version synchronization if changed
- **Documentation**: Update relevant documentation for changes

This style guide ensures consistency, maintainability, and quality across the entire League Analysis MCP Server codebase while adhering to the strict development standards defined in .claude/CLAUDE.md.