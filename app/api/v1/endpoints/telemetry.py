from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
import fastf1
import pandas as pd
import numpy as np
from app.models.telemetry import (
    TelemetryPoint, LapTelemetryResponse, SessionTelemetryResponse,
    DriverComparisonResponse, TelemetrySummaryResponse, TrackDataResponse,
    StintTelemetryResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def safe_timedelta_to_seconds(value):
    """Safely convert pandas Timedelta to seconds"""
    if value is None or pd.isna(value):
        return None
    if hasattr(value, 'total_seconds'):
        return float(value.total_seconds())
    if isinstance(value, (int, float)):
        return float(value)
    return None

def safe_float_conversion(value, default=0.0):
    """Safely convert any value to float, handling Timedelta objects"""
    if value is None or pd.isna(value):
        return default
    if hasattr(value, 'total_seconds'):
        return float(value.total_seconds())
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def process_telemetry_data(telemetry_df: pd.DataFrame) -> List[TelemetryPoint]:
    """Convert FastF1 telemetry DataFrame to TelemetryPoint objects"""
    telemetry_points = []
    
    for _, row in telemetry_df.iterrows():
        point = TelemetryPoint(
            time=safe_float_conversion(row.get('SessionTime'), 0.0),
            distance=safe_float_conversion(row.get('Distance')) if pd.notna(row.get('Distance')) else None,
            x=safe_float_conversion(row.get('X')) if pd.notna(row.get('X')) else None,
            y=safe_float_conversion(row.get('Y')) if pd.notna(row.get('Y')) else None,
            z=safe_float_conversion(row.get('Z')) if pd.notna(row.get('Z')) else None,
            speed=safe_float_conversion(row.get('Speed')) if pd.notna(row.get('Speed')) else None,
            rpm=int(safe_float_conversion(row.get('RPM'), 0)) if pd.notna(row.get('RPM')) else None,
            n_gear=int(safe_float_conversion(row.get('nGear'), 0)) if pd.notna(row.get('nGear')) else None,
            throttle=safe_float_conversion(row.get('Throttle')) if pd.notna(row.get('Throttle')) else None,
            brake=bool(row.get('Brake', False)) if pd.notna(row.get('Brake')) else None,
            drs=int(safe_float_conversion(row.get('DRS'), 0)) if pd.notna(row.get('DRS')) else None,
            steering=safe_float_conversion(row.get('Steering')) if pd.notna(row.get('Steering')) else None
        )
        telemetry_points.append(point)
    
    return telemetry_points

def calculate_lap_statistics(telemetry_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate lap statistics from telemetry data"""
    if telemetry_df.empty:
        return {}
    
    stats = {}
    
    # Speed statistics
    if 'Speed' in telemetry_df.columns:
        speeds = telemetry_df['Speed'].dropna()
        if not speeds.empty:
            stats['max_speed'] = safe_float_conversion(speeds.max())
            stats['avg_speed'] = safe_float_conversion(speeds.mean())
    
    # RPM statistics
    if 'RPM' in telemetry_df.columns:
        rpms = telemetry_df['RPM'].dropna()
        if not rpms.empty:
            stats['max_rpm'] = int(safe_float_conversion(rpms.max(), 0))
            stats['avg_rpm'] = safe_float_conversion(rpms.mean())
    
    # Throttle statistics
    if 'Throttle' in telemetry_df.columns:
        throttles = telemetry_df['Throttle'].dropna()
        if not throttles.empty:
            stats['throttle_percentage'] = safe_float_conversion(throttles.mean())
    
    # Brake statistics
    if 'Brake' in telemetry_df.columns:
        brakes = telemetry_df['Brake'].dropna()
        if not brakes.empty:
            stats['brake_percentage'] = safe_float_conversion((brakes > 0).mean() * 100)
    
    # DRS statistics
    if 'DRS' in telemetry_df.columns:
        drs = telemetry_df['DRS'].dropna()
        if not drs.empty:
            stats['drs_percentage'] = safe_float_conversion((drs > 0).mean() * 100)
    
    # Gear changes
    if 'nGear' in telemetry_df.columns:
        gears = telemetry_df['nGear'].dropna()
        if not gears.empty:
            gear_changes = (gears.diff() != 0).sum()
            stats['gear_changes'] = int(safe_float_conversion(gear_changes, 0))
    
    return stats

@router.get("/session/{year}/{event}/{session}", response_model=SessionTelemetryResponse)
async def get_session_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    drivers: Optional[str] = Query(None, description="Comma-separated driver abbreviations (e.g., 'VER,HAM')"),
    laps: Optional[str] = Query(None, description="Comma-separated lap numbers (e.g., '1,5,10')"),
    max_laps_per_driver: int = Query(5, description="Maximum number of laps per driver to return"),
):
    """
    Get comprehensive telemetry data for a session.
    
    - **year**: Season year
    - **event**: Event name or round number  
    - **session**: Session type (R=Race, Q=Qualifying, S=Sprint, FP1/2/3=Practice)
    - **drivers**: Optional filter for specific drivers
    - **laps**: Optional filter for specific lap numbers
    - **max_laps_per_driver**: Limit number of laps returned per driver
    """
    try:
        logger.info(f"Fetching telemetry for: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Prepare session info
        session_info = {
            "year": year,
            "event": event,
            "session_type": session,
            "track_name": str(session_obj.event.get('EventName', 'Unknown')),
            "country": str(session_obj.event.get('Country', 'Unknown')),
            "date": session_obj.date.isoformat() if session_obj.date else None,
            "total_laps": len(session_obj.laps) if hasattr(session_obj, 'laps') else 0
        }
        
        # Filter drivers if specified
        available_drivers = session_obj.drivers
        if drivers:
            driver_list = [d.strip().upper() for d in drivers.split(',')]
            available_drivers = [d for d in available_drivers if d in driver_list]
        
        # Filter laps if specified
        lap_numbers = None
        if laps:
            lap_numbers = [int(l.strip()) for l in laps.split(',')]
        
        session_laps = []
        
        for driver in available_drivers:
            try:
                driver_laps = session_obj.laps.pick_drivers(driver)
                
                # Apply lap number filter
                if lap_numbers:
                    driver_laps = driver_laps[driver_laps['LapNumber'].isin(lap_numbers)]
                
                # Limit number of laps
                driver_laps = driver_laps.head(max_laps_per_driver)
                
                for _, lap in driver_laps.iterrows():
                    try:
                        # Get telemetry for this lap
                        lap_telemetry = lap.get_telemetry()
                        if lap_telemetry.empty:
                            continue
                        
                        # Add distance to telemetry
                        lap_telemetry = lap_telemetry.add_distance()
                        
                        # Process telemetry points
                        telemetry_points = process_telemetry_data(lap_telemetry)
                        
                        # Calculate statistics
                        lap_stats = calculate_lap_statistics(lap_telemetry)
                        
                        lap_response = LapTelemetryResponse(
                            driver=driver,
                            lap_number=int(lap.get('LapNumber', 0)),
                            lap_time=safe_timedelta_to_seconds(lap.get('LapTime')),
                            is_accurate=bool(lap.get('IsValid', True)),
                            telemetry_points=telemetry_points,
                            **lap_stats
                        )
                        
                        session_laps.append(lap_response)
                        
                    except Exception as lap_error:
                        logger.warning(f"Could not process lap {lap.get('LapNumber')} for {driver}: {lap_error}")
                        continue
                        
            except Exception as driver_error:
                logger.warning(f"Could not process driver {driver}: {driver_error}")
                continue
        
        if not session_laps:
            raise HTTPException(status_code=404, detail="No telemetry data found for the specified parameters")
        
        response = SessionTelemetryResponse(
            session_info=session_info,
            drivers=list(available_drivers),
            laps=session_laps
        )
        
        logger.info(f"Returning telemetry for {len(available_drivers)} drivers, {len(session_laps)} laps")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching session telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry: {str(e)}")

@router.get("/lap/{year}/{event}/{session}/{driver}/{lap_number}", response_model=LapTelemetryResponse)
async def get_lap_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver: str = Path(..., description="Driver abbreviation (e.g., 'VER', 'HAM')"),
    lap_number: int = Path(..., description="Lap number"),
):
    """
    Get detailed telemetry data for a specific lap.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type
    - **driver**: Driver abbreviation
    - **lap_number**: Specific lap number
    """
    try:
        logger.info(f"Fetching lap telemetry: {year} {event} {session} {driver} lap {lap_number}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get specific lap
        driver_laps = session_obj.laps.pick_drivers(driver.upper())
        specific_lap = driver_laps[driver_laps['LapNumber'] == lap_number]
        
        if specific_lap.empty:
            raise HTTPException(status_code=404, detail=f"Lap {lap_number} not found for driver {driver}")
        
        lap = specific_lap.iloc[0]
        
        # Get telemetry for this lap
        lap_telemetry = lap.get_telemetry()
        if lap_telemetry.empty:
            raise HTTPException(status_code=404, detail=f"No telemetry data available for lap {lap_number}")
        
        # Add distance to telemetry
        lap_telemetry = lap_telemetry.add_distance()
        
        # Process telemetry points
        telemetry_points = process_telemetry_data(lap_telemetry)
        
        # Calculate statistics
        lap_stats = calculate_lap_statistics(lap_telemetry)
        
        response = LapTelemetryResponse(
            driver=driver.upper(),
            lap_number=lap_number,
            lap_time=safe_timedelta_to_seconds(lap.get('LapTime')),
            is_accurate=bool(lap.get('IsValid', True)),
            telemetry_points=telemetry_points,
            **lap_stats
        )
        
        logger.info(f"Returning telemetry for {driver} lap {lap_number} with {len(telemetry_points)} data points")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching lap telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch lap telemetry: {str(e)}")

@router.get("/compare/{year}/{event}/{session}", response_model=DriverComparisonResponse)
async def compare_drivers_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver1: str = Query(..., description="First driver abbreviation"),
    driver2: str = Query(..., description="Second driver abbreviation"),
    lap_type: str = Query("fastest", description="Lap type to compare (fastest, first, last, specific)"),
    lap1: Optional[int] = Query(None, description="Specific lap number for driver 1"),
    lap2: Optional[int] = Query(None, description="Specific lap number for driver 2"),
):
    """
    Compare telemetry data between two drivers.
    
    - **driver1**: First driver abbreviation
    - **driver2**: Second driver abbreviation  
    - **lap_type**: Type of lap to compare (fastest, first, last, specific)
    - **lap1**: Specific lap number for driver 1 (if lap_type is 'specific')
    - **lap2**: Specific lap number for driver 2 (if lap_type is 'specific')
    """
    try:
        logger.info(f"Comparing drivers {driver1} vs {driver2}: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get laps for both drivers
        laps1 = session_obj.laps.pick_drivers(driver1.upper())
        laps2 = session_obj.laps.pick_drivers(driver2.upper())
        
        if laps1.empty:
            raise HTTPException(status_code=404, detail=f"No laps found for driver {driver1}")
        if laps2.empty:
            raise HTTPException(status_code=404, detail=f"No laps found for driver {driver2}")
        
        # Select laps based on type
        if lap_type == "fastest":
            lap1_data = laps1.pick_fastest()
            lap2_data = laps2.pick_fastest()
        elif lap_type == "first":
            lap1_data = laps1.iloc[0]
            lap2_data = laps2.iloc[0]
        elif lap_type == "last":
            lap1_data = laps1.iloc[-1]
            lap2_data = laps2.iloc[-1]
        elif lap_type == "specific":
            if lap1 is None or lap2 is None:
                raise HTTPException(status_code=400, detail="Lap numbers required for specific lap comparison")
            lap1_data = laps1[laps1['LapNumber'] == lap1].iloc[0]
            lap2_data = laps2[laps2['LapNumber'] == lap2].iloc[0]
        else:
            raise HTTPException(status_code=400, detail="Invalid lap_type. Use: fastest, first, last, or specific")
        
        # Get telemetry for both laps
        telemetry1 = lap1_data.get_telemetry().add_distance()
        telemetry2 = lap2_data.get_telemetry().add_distance()
        
        # Process telemetry data
        points1 = process_telemetry_data(telemetry1)
        points2 = process_telemetry_data(telemetry2)
        
        # Calculate statistics
        stats1 = calculate_lap_statistics(telemetry1)
        stats2 = calculate_lap_statistics(telemetry2)
        
        # Create lap responses
        lap1_response = LapTelemetryResponse(
            driver=driver1.upper(),
            lap_number=int(lap1_data.get('LapNumber', 0)),
            lap_time=safe_timedelta_to_seconds(lap1_data.get('LapTime')),
            is_accurate=bool(lap1_data.get('IsValid', True)),
            telemetry_points=points1,
            **stats1
        )
        
        lap2_response = LapTelemetryResponse(
            driver=driver2.upper(),
            lap_number=int(lap2_data.get('LapNumber', 0)),
            lap_time=safe_timedelta_to_seconds(lap2_data.get('LapTime')),
            is_accurate=bool(lap2_data.get('IsValid', True)),
            telemetry_points=points2,
            **stats2
        )
        
        # Calculate comparison statistics
        comparison_stats = {
            "time_difference": (lap1_response.lap_time or 0) - (lap2_response.lap_time or 0),
            "speed_difference": {
                "max_speed_diff": (stats1.get('max_speed', 0) - stats2.get('max_speed', 0)),
                "avg_speed_diff": (stats1.get('avg_speed', 0) - stats2.get('avg_speed', 0))
            },
            "driving_style": {
                "throttle_diff": (stats1.get('throttle_percentage', 0) - stats2.get('throttle_percentage', 0)),
                "brake_usage_diff": (stats1.get('brake_percentage', 0) - stats2.get('brake_percentage', 0)),
                "drs_usage_diff": (stats1.get('drs_percentage', 0) - stats2.get('drs_percentage', 0))
            }
        }
        
        response = DriverComparisonResponse(
            driver_1=driver1.upper(),
            driver_2=driver2.upper(),
            lap_1=lap1_response,
            lap_2=lap2_response,
            comparison_stats=comparison_stats
        )
        
        logger.info(f"Returning comparison between {driver1} and {driver2}")
        return response
        
    except Exception as e:
        logger.error(f"Error comparing drivers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare drivers: {str(e)}")

@router.get("/summary/{year}/{event}/{session}/{driver}", response_model=TelemetrySummaryResponse)
async def get_driver_telemetry_summary(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver: str = Path(..., description="Driver abbreviation"),
):
    """
    Get comprehensive telemetry summary for a driver in a session.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type
    - **driver**: Driver abbreviation
    """
    try:
        logger.info(f"Fetching telemetry summary: {year} {event} {session} {driver}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get all laps for the driver
        driver_laps = session_obj.laps.pick_drivers(driver.upper())
        
        if driver_laps.empty:
            raise HTTPException(status_code=404, detail=f"No laps found for driver {driver}")
        
        # Get fastest lap details
        fastest_lap = driver_laps.pick_fastest()
        fastest_telemetry = fastest_lap.get_telemetry().add_distance()
        fastest_points = process_telemetry_data(fastest_telemetry)
        fastest_stats = calculate_lap_statistics(fastest_telemetry)
        
        fastest_lap_response = LapTelemetryResponse(
            driver=driver.upper(),
            lap_number=int(fastest_lap.get('LapNumber', 0)),
            lap_time=safe_timedelta_to_seconds(fastest_lap.get('LapTime')),
            is_accurate=bool(fastest_lap.get('IsValid', True)),
            telemetry_points=fastest_points,
            **fastest_stats
        )
        
        # Calculate session-wide statistics
        all_speeds = []
        all_rpms = []
        all_throttles = []
        all_brakes = []
        all_drs = []
        all_gear_changes = 0
        total_distance = 0
        
        for _, lap in driver_laps.iterrows():
            try:
                lap_tel = lap.get_telemetry()
                if not lap_tel.empty:
                    if 'Speed' in lap_tel.columns:
                        all_speeds.extend(lap_tel['Speed'].dropna().tolist())
                    if 'RPM' in lap_tel.columns:
                        all_rpms.extend(lap_tel['RPM'].dropna().tolist())
                    if 'Throttle' in lap_tel.columns:
                        all_throttles.extend(lap_tel['Throttle'].dropna().tolist())
                    if 'Brake' in lap_tel.columns:
                        all_brakes.extend(lap_tel['Brake'].dropna().tolist())
                    if 'DRS' in lap_tel.columns:
                        all_drs.extend(lap_tel['DRS'].dropna().tolist())
                    if 'nGear' in lap_tel.columns:
                        gears = lap_tel['nGear'].dropna()
                        all_gear_changes += (gears.diff() != 0).sum()
                    
                    lap_tel_with_dist = lap_tel.add_distance()
                    if 'Distance' in lap_tel_with_dist.columns:
                        lap_distance = lap_tel_with_dist['Distance'].max()
                        if pd.notna(lap_distance):
                            total_distance += lap_distance
            except:
                continue
        
        # Calculate averages and metrics
        session_max_speed = max(all_speeds) if all_speeds else None
        session_avg_speed = np.mean(all_speeds) if all_speeds else None
        session_max_rpm = max(all_rpms) if all_rpms else None
        avg_throttle_usage = np.mean(all_throttles) if all_throttles else None
        avg_brake_usage = np.mean([1 if b > 0 else 0 for b in all_brakes]) * 100 if all_brakes else None
        drs_usage_percentage = np.mean([1 if d > 0 else 0 for d in all_drs]) * 100 if all_drs else None
        gear_change_frequency = all_gear_changes / len(driver_laps) if len(driver_laps) > 0 else None
        
        # Count aggressive braking (sudden brake applications)
        aggressive_braking_count = 0
        for _, lap in driver_laps.iterrows():
            try:
                lap_tel = lap.get_telemetry()
                if 'Brake' in lap_tel.columns:
                    brake_diff = lap_tel['Brake'].diff()
                    aggressive_braking_count += (brake_diff > 50).sum()  # Threshold for aggressive braking
            except:
                continue
        
        response = TelemetrySummaryResponse(
            driver=driver.upper(),
            session_type=session,
            total_laps=len(driver_laps),
            fastest_lap=fastest_lap_response,
            session_max_speed=session_max_speed,
            session_avg_speed=session_avg_speed,
            session_max_rpm=session_max_rpm,
            total_distance=total_distance,
            avg_throttle_usage=avg_throttle_usage,
            avg_brake_usage=avg_brake_usage,
            aggressive_braking_count=aggressive_braking_count,
            drs_usage_percentage=drs_usage_percentage,
            gear_change_frequency=gear_change_frequency
        )
        
        logger.info(f"Returning telemetry summary for {driver}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching telemetry summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry summary: {str(e)}")

@router.get("/fastest-lap/{year}/{event}/{session}", response_model=List[LapTelemetryResponse])
async def get_fastest_laps_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    limit: int = Query(10, description="Number of fastest laps to return"),
):
    """
    Get telemetry data for the fastest laps in a session.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type
    - **limit**: Number of fastest laps to return
    """
    try:
        logger.info(f"Fetching fastest laps telemetry: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get all laps and sort by lap time
        all_laps = session_obj.laps
        fastest_laps = all_laps.pick_fastest(limit)
        
        fastest_laps_response = []
        
        for _, lap in fastest_laps.iterrows():
            try:
                # Get telemetry for this lap
                lap_telemetry = lap.get_telemetry().add_distance()
                
                if lap_telemetry.empty:
                    continue
                
                # Process telemetry points
                telemetry_points = process_telemetry_data(lap_telemetry)
                
                # Calculate statistics
                lap_stats = calculate_lap_statistics(lap_telemetry)
                
                lap_response = LapTelemetryResponse(
                    driver=str(lap.get('Driver', 'Unknown')),
                    lap_number=int(lap.get('LapNumber', 0)),
                    lap_time=safe_timedelta_to_seconds(lap.get('LapTime')),
                    is_accurate=bool(lap.get('IsValid', True)),
                    telemetry_points=telemetry_points,
                    **lap_stats
                )
                
                fastest_laps_response.append(lap_response)
                
            except Exception as lap_error:
                logger.warning(f"Could not process fastest lap: {lap_error}")
                continue
        
        if not fastest_laps_response:
            raise HTTPException(status_code=404, detail="No fastest lap telemetry data found")
        
        logger.info(f"Returning {len(fastest_laps_response)} fastest laps with telemetry")
        return fastest_laps_response
        
    except Exception as e:
        logger.error(f"Error fetching fastest laps telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fastest laps telemetry: {str(e)}")

@router.get("/stint/{year}/{event}/{session}/{driver}", response_model=List[StintTelemetryResponse])
async def get_stint_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver: str = Path(..., description="Driver abbreviation"),
):
    """
    Get telemetry data organized by tire stints for a driver.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type
    - **driver**: Driver abbreviation
    """
    try:
        logger.info(f"Fetching stint telemetry: {year} {event} {session} {driver}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        # Get all laps for the driver
        driver_laps = session_obj.laps.pick_drivers(driver.upper())
        
        if driver_laps.empty:
            raise HTTPException(status_code=404, detail=f"No laps found for driver {driver}")
        
        # Group laps by tire compound to identify stints
        stints = []
        current_stint = []
        current_compound = None
        stint_number = 1
        
        for _, lap in driver_laps.iterrows():
            compound = lap.get('Compound', 'Unknown')
            
            if compound != current_compound:
                # Start new stint
                if current_stint:
                    stints.append({
                        'stint_number': stint_number,
                        'compound': current_compound,
                        'laps': current_stint
                    })
                    stint_number += 1
                
                current_stint = [lap]
                current_compound = compound
            else:
                current_stint.append(lap)
        
        # Add the last stint
        if current_stint:
            stints.append({
                'stint_number': stint_number,
                'compound': current_compound,
                'laps': current_stint
            })
        
        stint_responses = []
        
        for stint in stints:
            stint_laps_response = []
            lap_times = []
            
            for lap in stint['laps']:
                try:
                    # Get telemetry for this lap
                    lap_telemetry = lap.get_telemetry().add_distance()
                    
                    if lap_telemetry.empty:
                        continue
                    
                    # Process telemetry points
                    telemetry_points = process_telemetry_data(lap_telemetry)
                    
                    # Calculate statistics
                    lap_stats = calculate_lap_statistics(lap_telemetry)
                    
                    lap_response = LapTelemetryResponse(
                        driver=driver.upper(),
                        lap_number=int(lap.get('LapNumber', 0)),
                        lap_time=safe_timedelta_to_seconds(lap.get('LapTime')),
                        is_accurate=bool(lap.get('IsValid', True)),
                        telemetry_points=telemetry_points,
                        **lap_stats
                    )
                    
                    stint_laps_response.append(lap_response)
                    
                    if lap_response.lap_time:
                        lap_times.append(lap_response.lap_time)
                        
                except Exception as lap_error:
                    logger.warning(f"Could not process stint lap: {lap_error}")
                    continue
            
            if not stint_laps_response:
                continue
            
            # Calculate stint statistics
            avg_lap_time = np.mean(lap_times) if lap_times else None
            fastest_lap_time = min(lap_times) if lap_times else None
            
            # Calculate tire degradation (time increase per lap)
            tire_degradation = None
            if len(lap_times) > 1:
                # Simple linear regression to find degradation rate
                lap_indices = list(range(len(lap_times)))
                degradation_slope = np.polyfit(lap_indices, lap_times, 1)[0] if len(lap_times) > 1 else 0
                tire_degradation = degradation_slope
            
            # Calculate stint averages
            all_speeds = []
            all_throttles = []
            all_brakes = []
            
            for lap_resp in stint_laps_response:
                for point in lap_resp.telemetry_points:
                    if point.speed:
                        all_speeds.append(point.speed)
                    if point.throttle:
                        all_throttles.append(point.throttle)
                    if point.brake is not None:
                        all_brakes.append(1 if point.brake else 0)
            
            stint_response = StintTelemetryResponse(
                driver=driver.upper(),
                stint_number=stint['stint_number'],
                start_lap=int(stint['laps'][0].get('LapNumber', 0)),
                end_lap=int(stint['laps'][-1].get('LapNumber', 0)),
                tire_compound=stint['compound'],
                tire_age=len(stint['laps']),
                stint_laps=stint_laps_response,
                avg_lap_time=avg_lap_time,
                fastest_lap_time=fastest_lap_time,
                tire_degradation=tire_degradation,
                avg_speed=np.mean(all_speeds) if all_speeds else None,
                avg_throttle=np.mean(all_throttles) if all_throttles else None,
                avg_brake_usage=np.mean(all_brakes) * 100 if all_brakes else None
            )
            
            stint_responses.append(stint_response)
        
        if not stint_responses:
            raise HTTPException(status_code=404, detail="No stint telemetry data found")
        
        logger.info(f"Returning {len(stint_responses)} stints for {driver}")
        return stint_responses
        
    except Exception as e:
        logger.error(f"Error fetching stint telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stint telemetry: {str(e)}")

@router.get("/track-analysis/{year}/{event}", response_model=TrackDataResponse)
async def get_track_telemetry_analysis(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Query("R", description="Session type for analysis (R, Q, S, FP1, FP2, FP3)"),
):
    """
    Get track analysis based on telemetry data from all drivers.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type for analysis
    """
    try:
        logger.info(f"Fetching track analysis: {year} {event} {session}")
        
        # Get session using FastF1
        session_obj = fastf1.get_session(year, event, session)
        session_obj.load()
        
        track_name = str(session_obj.event.get('EventName', 'Unknown'))
        
        # Collect telemetry data from all drivers
        all_telemetry = []
        
        for driver in session_obj.drivers:
            try:
                driver_laps = session_obj.laps.pick_drivers(driver)
                fastest_lap = driver_laps.pick_fastest()
                lap_telemetry = fastest_lap.get_telemetry().add_distance()
                
                if not lap_telemetry.empty:
                    all_telemetry.append(lap_telemetry)
                    
            except Exception:
                continue
        
        if not all_telemetry:
            raise HTTPException(status_code=404, detail="No telemetry data found for track analysis")
        
        # Combine all telemetry data
        combined_telemetry = pd.concat(all_telemetry, ignore_index=True)
        
        # Calculate track length
        track_length = None
        if 'Distance' in combined_telemetry.columns:
            track_length = combined_telemetry['Distance'].max()
        
        # Analyze speed zones (divide track into segments)
        speed_zones = []
        braking_zones = []
        drs_zones = []
        
        if 'Distance' in combined_telemetry.columns and 'Speed' in combined_telemetry.columns:
            # Divide track into 20 segments for analysis
            distance_bins = pd.cut(combined_telemetry['Distance'], bins=20, labels=False)
            
            for bin_num in range(20):
                bin_data = combined_telemetry[distance_bins == bin_num]
                
                if not bin_data.empty:
                    avg_speed = bin_data['Speed'].mean()
                    max_speed = bin_data['Speed'].max()
                    min_distance = bin_data['Distance'].min()
                    max_distance = bin_data['Distance'].max()
                    
                    # Classify speed zones
                    if avg_speed > 250:
                        zone_type = "high_speed"
                    elif avg_speed > 150:
                        zone_type = "medium_speed"
                    else:
                        zone_type = "low_speed"
                    
                    speed_zone = {
                        "zone_number": bin_num + 1,
                        "start_distance": safe_float_conversion(min_distance),
                        "end_distance": safe_float_conversion(max_distance),
                        "zone_type": zone_type,
                        "avg_speed": safe_float_conversion(avg_speed),
                        "max_speed": safe_float_conversion(max_speed)
                    }
                    speed_zones.append(speed_zone)
                    
                    # Identify braking zones (significant speed drops)
                    if 'Brake' in bin_data.columns:
                        brake_percentage = (bin_data['Brake'] > 0).mean()
                        if brake_percentage > 0.3:  # More than 30% braking
                            braking_zone = {
                                "zone_number": len(braking_zones) + 1,
                                "start_distance": safe_float_conversion(min_distance),
                                "end_distance": safe_float_conversion(max_distance),
                                "brake_intensity": safe_float_conversion(brake_percentage * 100),
                                "avg_speed": safe_float_conversion(avg_speed)
                            }
                            braking_zones.append(braking_zone)
                    
                    # Identify DRS zones
                    if 'DRS' in bin_data.columns:
                        drs_percentage = (bin_data['DRS'] > 0).mean()
                        if drs_percentage > 0.5:  # More than 50% DRS usage
                            drs_zone = {
                                "zone_number": len(drs_zones) + 1,
                                "start_distance": safe_float_conversion(min_distance),
                                "end_distance": safe_float_conversion(max_distance),
                                "drs_usage": safe_float_conversion(drs_percentage * 100),
                                "avg_speed": safe_float_conversion(avg_speed)
                            }
                            drs_zones.append(drs_zone)
        
        # Estimate corner count (number of low-speed zones)
        corner_count = len([zone for zone in speed_zones if zone["zone_type"] == "low_speed"])
        
        response = TrackDataResponse(
            track_name=track_name,
            track_length=track_length,
            corner_count=corner_count,
            speed_zones=speed_zones,
            braking_zones=braking_zones,
            drs_zones=drs_zones
        )
        
        logger.info(f"Returning track analysis for {track_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching track analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch track analysis: {str(e)}") 