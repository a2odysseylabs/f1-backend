from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
import fastf1
from fastf1.ergast import Ergast
import pandas as pd
from app.models.results import RaceResultResponse, QualifyingResultResponse, SprintResultResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Ergast API client
ergast = Ergast()

@router.get("/race/{year}", response_model=List[RaceResultResponse])
async def get_race_results(
    year: int = Path(..., description="Season year"),
    round_number: Optional[int] = Query(None, description="Specific round number"),
    driver: Optional[str] = Query(None, description="Filter by driver ID"),
    constructor: Optional[str] = Query(None, description="Filter by constructor ID"),
):
    """
    Get race results for a season or specific race.
    
    - **year**: Season year
    - **round_number**: Optional specific round number
    - **driver**: Optional filter by driver
    - **constructor**: Optional filter by constructor
    """
    try:
        logger.info(f"Fetching race results for year: {year}, round: {round_number}")
        
        # Fetch race results using Ergast
        results_response = ergast.get_race_results(
            season=year, 
            round=round_number, 
            driver=driver, 
            constructor=constructor
        )
        
        if not results_response.content:
            raise HTTPException(status_code=404, detail=f"No race results found for {year}")
        
        all_results = []
        
        # Process all races in the response
        for i, race_info in results_response.description.iterrows():
            race_results = results_response.content[i]
            
            for _, result in race_results.iterrows():
                result_data = {
                    "season": int(race_info.get('season', year)),
                    "round": int(race_info.get('round', 0)),
                    "race_name": str(race_info.get('raceName', '')),
                    "circuit_name": str(race_info.get('circuitName', '')),
                    "race_date": race_info.get('raceDate').isoformat() if pd.notna(race_info.get('raceDate')) else None,
                    "position": int(result.get('position', 0)) if pd.notna(result.get('position')) else None,
                    "position_text": str(result.get('positionText', '')),
                    "points": float(result.get('points', 0.0)),
                    "driver_id": str(result.get('driverId', '')),
                    "driver_code": str(result.get('driverCode', '')) if pd.notna(result.get('driverCode')) else None,
                    "driver_number": int(result.get('driverNumber', 0)) if pd.notna(result.get('driverNumber')) else None,
                    "given_name": str(result.get('givenName', '')),
                    "family_name": str(result.get('familyName', '')),
                    "constructor_id": str(result.get('constructorId', '')),
                    "constructor_name": str(result.get('constructorName', '')),
                    "grid_position": int(result.get('grid', 0)) if pd.notna(result.get('grid')) else None,
                    "laps_completed": int(result.get('laps', 0)) if pd.notna(result.get('laps')) else None,
                    "status": str(result.get('status', '')),
                    "fastest_lap_rank": int(result.get('fastestLapRank', 0)) if pd.notna(result.get('fastestLapRank')) else None,
                    "fastest_lap_time": str(result.get('fastestLapTime', '')) if pd.notna(result.get('fastestLapTime')) else None
                }
                all_results.append(result_data)
        
        logger.info(f"Returning {len(all_results)} race results")
        return all_results
        
    except Exception as e:
        logger.error(f"Error fetching race results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch race results: {str(e)}")

@router.get("/qualifying/{year}", response_model=List[QualifyingResultResponse])
async def get_qualifying_results(
    year: int = Path(..., description="Season year"),
    round_number: Optional[int] = Query(None, description="Specific round number"),
    driver: Optional[str] = Query(None, description="Filter by driver ID"),
    constructor: Optional[str] = Query(None, description="Filter by constructor ID"),
):
    """
    Get qualifying results for a season or specific race.
    
    - **year**: Season year
    - **round_number**: Optional specific round number
    - **driver**: Optional filter by driver
    - **constructor**: Optional filter by constructor
    """
    try:
        logger.info(f"Fetching qualifying results for year: {year}, round: {round_number}")
        
        # Fetch qualifying results using Ergast
        results_response = ergast.get_qualifying_results(
            season=year, 
            round=round_number, 
            driver=driver, 
            constructor=constructor
        )
        
        if not results_response.content:
            raise HTTPException(status_code=404, detail=f"No qualifying results found for {year}")
        
        all_results = []
        
        # Process all qualifying sessions in the response
        for i, race_info in results_response.description.iterrows():
            qualifying_results = results_response.content[i]
            
            for _, result in qualifying_results.iterrows():
                result_data = {
                    "season": int(race_info.get('season', year)),
                    "round": int(race_info.get('round', 0)),
                    "race_name": str(race_info.get('raceName', '')),
                    "circuit_name": str(race_info.get('circuitName', '')),
                    "race_date": race_info.get('raceDate').isoformat() if pd.notna(race_info.get('raceDate')) else None,
                    "position": int(result.get('position', 0)),
                    "driver_id": str(result.get('driverId', '')),
                    "driver_code": str(result.get('driverCode', '')) if pd.notna(result.get('driverCode')) else None,
                    "driver_number": int(result.get('driverNumber', 0)) if pd.notna(result.get('driverNumber')) else None,
                    "given_name": str(result.get('givenName', '')),
                    "family_name": str(result.get('familyName', '')),
                    "constructor_id": str(result.get('constructorId', '')),
                    "constructor_name": str(result.get('constructorName', '')),
                    "q1_time": str(result.get('Q1', '')) if pd.notna(result.get('Q1')) else None,
                    "q2_time": str(result.get('Q2', '')) if pd.notna(result.get('Q2')) else None,
                    "q3_time": str(result.get('Q3', '')) if pd.notna(result.get('Q3')) else None
                }
                all_results.append(result_data)
        
        logger.info(f"Returning {len(all_results)} qualifying results")
        return all_results
        
    except Exception as e:
        logger.error(f"Error fetching qualifying results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch qualifying results: {str(e)}")

@router.get("/sprint/{year}", response_model=List[SprintResultResponse])
async def get_sprint_results(
    year: int = Path(..., description="Season year"),
    round_number: Optional[int] = Query(None, description="Specific round number"),
    driver: Optional[str] = Query(None, description="Filter by driver ID"),
    constructor: Optional[str] = Query(None, description="Filter by constructor ID"),
):
    """
    Get sprint race results for a season or specific race.
    
    - **year**: Season year
    - **round_number**: Optional specific round number
    - **driver**: Optional filter by driver
    - **constructor**: Optional filter by constructor
    """
    try:
        logger.info(f"Fetching sprint results for year: {year}, round: {round_number}")
        
        # Fetch sprint results using Ergast
        results_response = ergast.get_sprint_results(
            season=year, 
            round=round_number, 
            driver=driver, 
            constructor=constructor
        )
        
        if not results_response.content:
            raise HTTPException(status_code=404, detail=f"No sprint results found for {year}")
        
        all_results = []
        
        # Process all sprint races in the response
        for i, race_info in results_response.description.iterrows():
            sprint_results = results_response.content[i]
            
            for _, result in sprint_results.iterrows():
                result_data = {
                    "season": int(race_info.get('season', year)),
                    "round": int(race_info.get('round', 0)),
                    "race_name": str(race_info.get('raceName', '')),
                    "circuit_name": str(race_info.get('circuitName', '')),
                    "race_date": race_info.get('raceDate').isoformat() if pd.notna(race_info.get('raceDate')) else None,
                    "position": int(result.get('position', 0)) if pd.notna(result.get('position')) else None,
                    "position_text": str(result.get('positionText', '')),
                    "points": float(result.get('points', 0.0)),
                    "driver_id": str(result.get('driverId', '')),
                    "driver_code": str(result.get('driverCode', '')) if pd.notna(result.get('driverCode')) else None,
                    "driver_number": int(result.get('driverNumber', 0)) if pd.notna(result.get('driverNumber')) else None,
                    "given_name": str(result.get('givenName', '')),
                    "family_name": str(result.get('familyName', '')),
                    "constructor_id": str(result.get('constructorId', '')),
                    "constructor_name": str(result.get('constructorName', '')),
                    "grid_position": int(result.get('grid', 0)) if pd.notna(result.get('grid')) else None,
                    "laps_completed": int(result.get('laps', 0)) if pd.notna(result.get('laps')) else None,
                    "status": str(result.get('status', ''))
                }
                all_results.append(result_data)
        
        logger.info(f"Returning {len(all_results)} sprint results")
        return all_results
        
    except Exception as e:
        logger.error(f"Error fetching sprint results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sprint results: {str(e)}")

@router.get("/session/{year}/{event}/{session}")
async def get_session_results(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
):
    """
    Get results from a specific session using FastF1.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type (R=Race, Q=Qualifying, S=Sprint, FP1/2/3=Practice)
    """
    try:
        logger.info(f"Fetching session results for: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get session results
        results = session_obj.results
        
        if results.empty:
            raise HTTPException(status_code=404, detail=f"No results found for session {session} in {event} {year}")
        
        session_results = []
        for _, result in results.iterrows():
            result_data = {
                "position": int(result.get('Position', 0)) if pd.notna(result.get('Position')) else None,
                "driver_number": int(result.get('DriverNumber', 0)) if pd.notna(result.get('DriverNumber')) else None,
                "driver_abbreviation": str(result.get('Abbreviation', '')) if pd.notna(result.get('Abbreviation')) else None,
                "driver_name": f"{result.get('FirstName', '')} {result.get('LastName', '')}".strip(),
                "team_name": str(result.get('TeamName', '')) if pd.notna(result.get('TeamName')) else None,
                "time": str(result.get('Time', '')) if pd.notna(result.get('Time')) else None,
                "status": str(result.get('Status', '')) if pd.notna(result.get('Status')) else None,
                "points": float(result.get('Points', 0.0)) if pd.notna(result.get('Points')) else None
            }
            session_results.append(result_data)
        
        logger.info(f"Returning {len(session_results)} session results")
        return {
            "session_info": {
                "year": year,
                "event": event,
                "session": session,
                "session_name": session_obj.name,
                "date": session_obj.date.isoformat() if hasattr(session_obj, 'date') and session_obj.date else None
            },
            "results": session_results
        }
        
    except Exception as e:
        logger.error(f"Error fetching session results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session results: {str(e)}")

@router.get("/current/race", response_model=List[RaceResultResponse])
async def get_current_race_results(
    round_number: Optional[int] = Query(None, description="Specific round number"),
):
    """
    Get current season race results.
    """
    import datetime
    current_year = datetime.datetime.now().year
    return await get_race_results(current_year, round_number, None, None)

@router.get("/current/qualifying", response_model=List[QualifyingResultResponse])
async def get_current_qualifying_results(
    round_number: Optional[int] = Query(None, description="Specific round number"),
):
    """
    Get current season qualifying results.
    """
    import datetime
    current_year = datetime.datetime.now().year
    return await get_qualifying_results(current_year, round_number, None, None) 