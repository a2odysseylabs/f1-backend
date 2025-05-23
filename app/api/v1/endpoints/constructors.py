from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from fastf1.ergast import Ergast
import pandas as pd
from app.models.constructors import ConstructorResponse, ConstructorStandingsResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Ergast API client
ergast = Ergast()

@router.get("/", response_model=List[ConstructorResponse])
async def get_constructors(
    year: int = Query(..., description="Season year", example=2024),
):
    """
    Get all constructors/teams for a specific season.
    
    - **year**: Season year
    """
    try:
        logger.info(f"Fetching constructors for year: {year}")
        
        # Fetch constructors using Ergast API
        constructors_response = ergast.get_constructor_info(season=year)
        
        if constructors_response.empty:
            raise HTTPException(status_code=404, detail=f"No constructors found for year {year}")
        
        constructors_data = []
        for _, constructor in constructors_response.iterrows():
            constructor_info = {
                "constructor_id": str(constructor.get('constructorId', '')),
                "constructor_name": str(constructor.get('constructorName', '')),
                "nationality": str(constructor.get('constructorNationality', '')),
                "constructor_url": str(constructor.get('constructorUrl', '')) if pd.notna(constructor.get('constructorUrl')) else None
            }
            constructors_data.append(constructor_info)
        
        logger.info(f"Returning {len(constructors_data)} constructors for {year}")
        return constructors_data
        
    except Exception as e:
        logger.error(f"Error fetching constructors for {year}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructors: {str(e)}")

@router.get("/{constructor_id}/info", response_model=ConstructorResponse)
async def get_constructor_info(
    constructor_id: str = Path(..., description="Constructor identifier (e.g., 'mercedes', 'red_bull')"),
    year: Optional[int] = Query(None, description="Season year for additional context"),
):
    """
    Get detailed information about a specific constructor.
    
    - **constructor_id**: Constructor identifier (e.g., 'mercedes', 'red_bull')
    - **year**: Optional season year for context
    """
    try:
        logger.info(f"Fetching constructor info for: {constructor_id}")
        
        # Fetch specific constructor info using Ergast
        constructor_response = ergast.get_constructor_info(season=year, constructor=constructor_id)
        
        if constructor_response.empty:
            raise HTTPException(status_code=404, detail=f"Constructor {constructor_id} not found")
        
        constructor = constructor_response.iloc[0]
        constructor_info = {
            "constructor_id": str(constructor.get('constructorId', '')),
            "constructor_name": str(constructor.get('constructorName', '')),
            "nationality": str(constructor.get('constructorNationality', '')),
            "constructor_url": str(constructor.get('constructorUrl', '')) if pd.notna(constructor.get('constructorUrl')) else None
        }
        
        return constructor_info
        
    except Exception as e:
        logger.error(f"Error fetching constructor info for {constructor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor info: {str(e)}")

@router.get("/standings/{year}", response_model=List[ConstructorStandingsResponse])
async def get_constructor_standings(
    year: int = Path(..., description="Season year"),
    round_number: Optional[int] = Query(None, description="Specific round number for standings"),
):
    """
    Get constructor championship standings for a season.
    
    - **year**: Season year
    - **round_number**: Optional specific round number
    """
    try:
        logger.info(f"Fetching constructor standings for: {year}, round: {round_number}")
        
        # Fetch standings using Ergast
        standings_response = ergast.get_constructor_standings(season=year, round=round_number)
        
        if not standings_response.content:
            raise HTTPException(status_code=404, detail=f"No constructor standings found for {year}")
        
        # Get the latest standings (last element in content)
        latest_standings = standings_response.content[-1]
        
        standings_data = []
        for _, standing in latest_standings.iterrows():
            standing_info = {
                "position": int(standing.get('position', 0)),
                "points": float(standing.get('points', 0.0)),
                "wins": int(standing.get('wins', 0)),
                "constructor_id": str(standing.get('constructorId', '')),
                "constructor_name": str(standing.get('constructorName', '')),
                "nationality": str(standing.get('constructorNationality', ''))
            }
            standings_data.append(standing_info)
        
        logger.info(f"Returning {len(standings_data)} constructor standings")
        return standings_data
        
    except Exception as e:
        logger.error(f"Error fetching constructor standings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor standings: {str(e)}")

@router.get("/{constructor_id}/drivers/{year}", response_model=List[dict])
async def get_constructor_drivers(
    constructor_id: str = Path(..., description="Constructor identifier"),
    year: int = Path(..., description="Season year"),
):
    """
    Get all drivers for a specific constructor in a given year.
    
    - **constructor_id**: Constructor identifier
    - **year**: Season year
    """
    try:
        logger.info(f"Fetching drivers for constructor {constructor_id} in {year}")
        
        # Fetch drivers for specific constructor using Ergast
        drivers_response = ergast.get_driver_info(season=year, constructor=constructor_id)
        
        if drivers_response.empty:
            raise HTTPException(status_code=404, detail=f"No drivers found for constructor {constructor_id} in {year}")
        
        drivers_data = []
        for _, driver in drivers_response.iterrows():
            driver_info = {
                "driver_id": str(driver.get('driverId', '')),
                "driver_number": int(driver.get('driverNumber', 0)) if pd.notna(driver.get('driverNumber')) else None,
                "driver_code": str(driver.get('driverCode', '')) if pd.notna(driver.get('driverCode')) else None,
                "given_name": str(driver.get('givenName', '')),
                "family_name": str(driver.get('familyName', '')),
                "nationality": str(driver.get('driverNationality', ''))
            }
            drivers_data.append(driver_info)
        
        logger.info(f"Returning {len(drivers_data)} drivers for constructor {constructor_id}")
        return drivers_data
        
    except Exception as e:
        logger.error(f"Error fetching drivers for constructor {constructor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor drivers: {str(e)}")

@router.get("/current", response_model=List[ConstructorResponse])
async def get_current_constructors(
):
    """
    Get current season constructors.
    """
    import datetime
    current_year = datetime.datetime.now().year
    return await get_constructors(current_year)

@router.get("/seasons", response_model=List[dict])
async def get_constructor_seasons(
    constructor_id: str = Query(..., description="Constructor identifier"),
):
    """
    Get all seasons a constructor participated in.
    
    - **constructor_id**: Constructor identifier
    """
    try:
        logger.info(f"Fetching seasons for constructor: {constructor_id}")
        
        # This would require a more complex query to get all seasons
        # For now, let's return the years the constructor was active
        # This is a simplified version - in reality, you'd want to implement
        # a more comprehensive search across all seasons
        
        seasons_data = []
        # Get constructor info without season filter to see all years
        constructor_response = ergast.get_constructor_info(constructor=constructor_id, limit=1000)
        
        if constructor_response.empty:
            raise HTTPException(status_code=404, detail=f"Constructor {constructor_id} not found")
        
        # This is a placeholder - you'd need to implement proper season tracking
        return [{"message": f"Constructor {constructor_id} found. Season details would be implemented with more complex queries."}]
        
    except Exception as e:
        logger.error(f"Error fetching seasons for constructor {constructor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor seasons: {str(e)}") 