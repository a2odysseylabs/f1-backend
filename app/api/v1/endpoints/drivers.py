from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
import fastf1
from fastf1.ergast import Ergast
import pandas as pd
from app.models.drivers import DriverResponse, DriverSessionResponse, DriverStandingsResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Ergast API client
ergast = Ergast()

@router.get("/", response_model=List[DriverResponse])
async def get_drivers(
    year: int = Query(..., description="Season year", example=2024),
    constructor: Optional[str] = Query(None, description="Filter by constructor ID"),
):
    """
    Get all drivers for a specific season.
    
    - **year**: Season year
    - **constructor**: Optional filter by constructor/team
    """
    try:
        logger.info(f"Fetching drivers for year: {year}")
        
        # Fetch drivers using Ergast API
        drivers_response = ergast.get_driver_info(season=year, constructor=constructor)
        
        if drivers_response.empty:
            raise HTTPException(status_code=404, detail=f"No drivers found for year {year}")
        
        drivers_data = []
        for _, driver in drivers_response.iterrows():
            driver_info = {
                "driver_id": str(driver.get('driverId', '')),
                "driver_number": int(driver.get('driverNumber', 0)) if pd.notna(driver.get('driverNumber')) else None,
                "driver_code": str(driver.get('driverCode', '')) if pd.notna(driver.get('driverCode')) else None,
                "given_name": str(driver.get('givenName', '')),
                "family_name": str(driver.get('familyName', '')),
                "date_of_birth": driver.get('dateOfBirth').isoformat() if pd.notna(driver.get('dateOfBirth')) else None,
                "nationality": str(driver.get('driverNationality', '')),
                "driver_url": str(driver.get('driverUrl', '')) if pd.notna(driver.get('driverUrl')) else None
            }
            drivers_data.append(driver_info)
        
        logger.info(f"Returning {len(drivers_data)} drivers for {year}")
        return drivers_data
        
    except Exception as e:
        logger.error(f"Error fetching drivers for {year}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch drivers: {str(e)}")

@router.get("/{driver_id}/info", response_model=DriverResponse)
async def get_driver_info(
    driver_id: str = Path(..., description="Driver identifier (e.g., 'hamilton', 'verstappen')"),
    year: Optional[int] = Query(None, description="Season year for additional context"),
):
    """
    Get detailed information about a specific driver.
    
    - **driver_id**: Driver identifier (e.g., 'hamilton', 'verstappen')
    - **year**: Optional season year for context
    """
    try:
        logger.info(f"Fetching driver info for: {driver_id}")
        
        # Fetch specific driver info using Ergast
        driver_response = ergast.get_driver_info(season=year, driver=driver_id)
        
        if driver_response.empty:
            raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
        
        driver = driver_response.iloc[0]
        driver_info = {
            "driver_id": str(driver.get('driverId', '')),
            "driver_number": int(driver.get('driverNumber', 0)) if pd.notna(driver.get('driverNumber')) else None,
            "driver_code": str(driver.get('driverCode', '')) if pd.notna(driver.get('driverCode')) else None,
            "given_name": str(driver.get('givenName', '')),
            "family_name": str(driver.get('familyName', '')),
            "date_of_birth": driver.get('dateOfBirth').isoformat() if pd.notna(driver.get('dateOfBirth')) else None,
            "nationality": str(driver.get('driverNationality', '')),
            "driver_url": str(driver.get('driverUrl', '')) if pd.notna(driver.get('driverUrl')) else None
        }
        
        return driver_info
        
    except Exception as e:
        logger.error(f"Error fetching driver info for {driver_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver info: {str(e)}")

@router.get("/session/{year}/{event}/{session}", response_model=List[DriverSessionResponse])
async def get_session_drivers(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
):
    """
    Get drivers who participated in a specific session.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type (R=Race, Q=Qualifying, S=Sprint, FP1/2/3=Practice)
    """
    try:
        logger.info(f"Fetching session drivers for: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get drivers from the session
        drivers_data = []
        for driver_abbr in session_obj.drivers:
            try:
                driver_info = session_obj.get_driver(driver_abbr)
                driver_data = {
                    "driver_abbreviation": str(driver_abbr),
                    "driver_number": int(driver_info['DriverNumber']) if pd.notna(driver_info.get('DriverNumber')) else None,
                    "given_name": str(driver_info.get('GivenName', '')),
                    "family_name": str(driver_info.get('FamilyName', '')),
                    "team_name": str(driver_info.get('TeamName', '')),
                    "team_color": str(driver_info.get('TeamColor', '')) if pd.notna(driver_info.get('TeamColor')) else None
                }
                drivers_data.append(driver_data)
            except Exception as driver_error:
                logger.warning(f"Could not get info for driver {driver_abbr}: {driver_error}")
                continue
        
        if not drivers_data:
            raise HTTPException(status_code=404, detail=f"No drivers found for session {session} in {event} {year}")
        
        logger.info(f"Returning {len(drivers_data)} drivers for session")
        return drivers_data
        
    except Exception as e:
        logger.error(f"Error fetching session drivers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session drivers: {str(e)}")

@router.get("/standings/{year}", response_model=List[DriverStandingsResponse])
async def get_driver_standings(
    year: int = Path(..., description="Season year"),
    round_number: Optional[int] = Query(None, description="Specific round number for standings"),
):
    """
    Get driver championship standings for a season.
    
    - **year**: Season year
    - **round_number**: Optional specific round number
    """
    try:
        logger.info(f"Fetching driver standings for: {year}, round: {round_number}")
        
        # Fetch standings using Ergast
        standings_response = ergast.get_driver_standings(season=year, round=round_number)
        
        if not standings_response.content:
            raise HTTPException(status_code=404, detail=f"No standings found for {year}")
        
        # Get the latest standings (last element in content)
        latest_standings = standings_response.content[-1]
        
        standings_data = []
        for _, standing in latest_standings.iterrows():
            standing_info = {
                "position": int(standing.get('position', 0)),
                "points": float(standing.get('points', 0.0)),
                "wins": int(standing.get('wins', 0)),
                "driver_id": str(standing.get('driverId', '')),
                "driver_code": str(standing.get('driverCode', '')) if pd.notna(standing.get('driverCode')) else None,
                "given_name": str(standing.get('givenName', '')),
                "family_name": str(standing.get('familyName', '')),
                "nationality": str(standing.get('driverNationality', ''))
            }
            standings_data.append(standing_info)
        
        logger.info(f"Returning {len(standings_data)} driver standings")
        return standings_data
        
    except Exception as e:
        logger.error(f"Error fetching driver standings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver standings: {str(e)}")

@router.get("/current", response_model=List[DriverResponse])
async def get_current_drivers(
    constructor: Optional[str] = Query(None, description="Filter by constructor ID"),
):
    """
    Get current season drivers.
    """
    import datetime
    current_year = datetime.datetime.now().year
    return await get_drivers(current_year, constructor) 