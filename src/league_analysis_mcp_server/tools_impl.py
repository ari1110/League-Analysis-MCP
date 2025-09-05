#!/usr/bin/env python3
"""
Implementation functions for MCP tools that can be imported and tested.

These are private implementation functions extracted from the MCP tool decorators
to enable proper testing and direct function access.
"""

import logging
from typing import Dict, Any, Optional
from yfpy import YahooFantasySportsQuery

from .data_enhancer import DataEnhancer

logger = logging.getLogger(__name__)


def _get_yahoo_query(league_id: str, game_id: Optional[str], sport: str, app_state: Dict[str, Any]) -> YahooFantasySportsQuery:
    """Create a Yahoo Fantasy Sports Query object."""
    auth_manager = app_state["auth_manager"]
    if not auth_manager.is_configured():
        raise ValueError("Yahoo authentication not configured. Run check_setup_status() to begin setup.")
    auth_credentials = auth_manager.get_auth_credentials()
    # Use game_id if provided, otherwise use current season
    if game_id:
        query_params = {**auth_credentials, 'game_id': game_id}
    else:
        query_params = {**auth_credentials, 'game_code': sport}
    return YahooFantasySportsQuery(
        league_id=league_id,
        **query_params
    )


def get_league_info_impl(league_id: str, sport: str, season: Optional[str], app_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implementation of get_league_info MCP tool.
    
    Args:
        league_id: Yahoo league ID
        sport: Sport code (nfl, nba, mlb, nhl)
        season: Specific season year (optional)
        app_state: Application state containing cache_manager, auth_manager, etc.
        
    Returns:
        League information and settings
    """
    try:
        cache_manager = app_state["cache_manager"]

        # Check cache first
        if season:
            cached_data = cache_manager.get_historical_data(sport, season, league_id, "league_info")
        else:
            cached_data = cache_manager.get_current_data(sport, league_id, "league_info")

        if cached_data:
            return cached_data

        # Get game_id for specific season if provided
        game_id = None
        if season:
            game_id = app_state["game_ids"].get(sport, {}).get(season)
            if not game_id:
                return {"error": f"No game_id found for {sport} {season}"}

        yahoo_query = _get_yahoo_query(league_id, game_id, sport, app_state)
        league_info = yahoo_query.get_league_info()

        # Use DataEnhancer for consistent, readable league information
        data_enhancer = DataEnhancer(yahoo_query, cache_manager)
        enhanced_league_info = data_enhancer.enhance_league_info(league_info)

        result = {
            "league_id": league_id,
            "sport": sport,
            "season": season or "current",
            **enhanced_league_info
        }

        # Cache the result
        if season:
            cache_manager.set_historical_data(sport, season, league_id, "league_info", result)
        else:
            cache_manager.set_current_data(sport, league_id, "league_info", result)

        return result

    except Exception as e:
        logger.error(f"Error getting league info: {e}")
        return {"error": str(e)}


def get_standings_impl(league_id: str, sport: str, season: Optional[str], app_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implementation of get_standings MCP tool.
    
    Args:
        league_id: Yahoo league ID
        sport: Sport code (nfl, nba, mlb, nhl)
        season: Specific season year (optional)
        app_state: Application state containing cache_manager, auth_manager, etc.
        
    Returns:
        League standings information
    """
    try:
        cache_manager = app_state["cache_manager"]

        # Check cache first
        if season:
            cached_data = cache_manager.get_historical_data(sport, season, league_id, "standings")
        else:
            cached_data = cache_manager.get_current_data(sport, league_id, "standings")

        if cached_data:
            return cached_data

        # Get game_id for specific season if provided
        game_id = None
        if season:
            game_id = app_state["game_ids"].get(sport, {}).get(season)
            if not game_id:
                return {"error": f"No game_id found for {sport} {season}"}

        yahoo_query = _get_yahoo_query(league_id, game_id, sport, app_state)
        standings = yahoo_query.get_league_standings()

        # Use DataEnhancer for consistent, readable team results
        data_enhancer = DataEnhancer(yahoo_query, cache_manager)
        teams_data = data_enhancer.enhance_data_batch(standings.teams, 'team')

        result = {
            "league_id": league_id,
            "sport": sport,
            "season": season or "current",
            "teams": teams_data
        }

        # Cache the result
        if season:
            cache_manager.set_historical_data(sport, season, league_id, "standings", result)
        else:
            cache_manager.set_current_data(sport, league_id, "standings", result)

        return result

    except Exception as e:
        logger.error(f"Error getting standings: {e}")
        return {"error": str(e)}
