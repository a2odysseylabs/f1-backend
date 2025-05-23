from typing import List, Union, Optional
from fastapi import APIRouter, HTTPException, Query, Path
import fastf1
import pandas as pd
from app.models.schedule import ScheduleResponse, EventResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[ScheduleResponse])
async def get_schedule(
    year: int = Query(..., description="Year of the season", example=2024),
    include_testing: bool = Query(False, description="Include testing sessions"),
):
    """
    Get the complete event schedule for a given year.
    
    - **year**: Season year (e.g., 2024)
    - **include_testing**: Whether to include pre-season testing events
    """
    try:
        logger.info(f"Fetching schedule for year: {year}")
        
        # Fetch schedule using FastF1
        schedule_df = fastf1.get_event_schedule(year, include_testing=include_testing)
        
        if schedule_df.empty:
            raise HTTPException(status_code=404, detail=f"No schedule found for year {year}")
        
        # Convert DataFrame to list of dictionaries
        schedule_data = []
        for _, row in schedule_df.iterrows():
            event_data = {
                "round_number": int(row.get('RoundNumber', 0)) if pd.notna(row.get('RoundNumber')) else None,
                "event_name": str(row.get('EventName', '')) if pd.notna(row.get('EventName')) else None,
                "event_date": row.get('EventDate').isoformat() if pd.notna(row.get('EventDate')) else None,
                "event_format": str(row.get('EventFormat', '')) if pd.notna(row.get('EventFormat')) else None,
                "session1_date": row.get('Session1Date').isoformat() if pd.notna(row.get('Session1Date')) else None,
                "session2_date": row.get('Session2Date').isoformat() if pd.notna(row.get('Session2Date')) else None,
                "session3_date": row.get('Session3Date').isoformat() if pd.notna(row.get('Session3Date')) else None,
                "session4_date": row.get('Session4Date').isoformat() if pd.notna(row.get('Session4Date')) else None,
                "session5_date": row.get('Session5Date').isoformat() if pd.notna(row.get('Session5Date')) else None,
                "f1_api_support": bool(row.get('F1ApiSupport', False)) if pd.notna(row.get('F1ApiSupport')) else False,
                "location": str(row.get('Location', '')) if pd.notna(row.get('Location')) else None,
                "country": str(row.get('Country', '')) if pd.notna(row.get('Country')) else None,
            }
            schedule_data.append(event_data)
        
        logger.info(f"Returning schedule for {year} with {len(schedule_data)} events")
        return schedule_data
        
    except Exception as e:
        logger.error(f"Error fetching schedule for {year}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch schedule: {str(e)}")

@router.get("/{year}/event/{event_identifier}", response_model=EventResponse)
async def get_event_details(
    year: int,
    event_identifier: Union[int, str] = Path(..., description="Event round number or name"),
):
    """
    Get detailed information about a specific event.
    
    - **year**: Season year
    - **event_identifier**: Round number (int) or event name (str)
    """
    try:
        logger.info(f"Fetching event details for year: {year}, event: {event_identifier}")
        
        # Get the event using FastF1
        if isinstance(event_identifier, int) or event_identifier.isdigit():
            event = fastf1.get_event(year, int(event_identifier))
        else:
            event = fastf1.get_event(year, event_identifier)
        
        # Convert event data to response format
        event_data = {
            "round_number": int(event.RoundNumber) if hasattr(event, 'RoundNumber') and pd.notna(event.RoundNumber) else None,
            "event_name": str(event.EventName) if hasattr(event, 'EventName') and pd.notna(event.EventName) else None,
            "event_date": event.EventDate.isoformat() if hasattr(event, 'EventDate') and pd.notna(event.EventDate) else None,
            "event_format": str(event.EventFormat) if hasattr(event, 'EventFormat') and pd.notna(event.EventFormat) else None,
            "location": str(event.Location) if hasattr(event, 'Location') and pd.notna(event.Location) else None,
            "country": str(event.Country) if hasattr(event, 'Country') and pd.notna(event.Country) else None,
            "f1_api_support": bool(event.F1ApiSupport) if hasattr(event, 'F1ApiSupport') and pd.notna(event.F1ApiSupport) else False,
            "sessions": []
        }
        
        # Add session information
        session_types = ['Session1', 'Session2', 'Session3', 'Session4', 'Session5']
        for session_type in session_types:
            date_attr = f"{session_type}Date"
            if hasattr(event, date_attr) and pd.notna(getattr(event, date_attr)):
                session_info = {
                    "session_name": session_type,
                    "session_date": getattr(event, date_attr).isoformat()
                }
                event_data["sessions"].append(session_info)
        
        return event_data
        
    except Exception as e:
        logger.error(f"Error fetching event details: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Event not found: {str(e)}")

@router.get("/current", response_model=List[ScheduleResponse])
async def get_current_schedule(
    include_testing: bool = Query(False, description="Include testing sessions"),
):
    """
    Get the current season schedule.
    """
    import datetime
    current_year = datetime.datetime.now().year
    return await get_schedule(current_year, include_testing) 