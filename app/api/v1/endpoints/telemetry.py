from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
import fastf1
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from app.models.telemetry import (
    TelemetryPoint, FastestLapTelemetryResponse, 
    TrackDominanceResponse, TrackSection
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def map_event_identifier(event: str):
    """Map event identifier to format expected by FastF1"""
    # If it's already a number, return as int
    try:
        return int(event)
    except ValueError:
        pass
    
    # If it's a string that looks like a number
    if event.isdigit():
        return int(event)
    
    # Otherwise return as string for event name
    return event

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
            speed=safe_float_conversion(row.get('Speed')) if pd.notna(row.get('Speed')) else None,
            rpm=int(safe_float_conversion(row.get('RPM'), 0)) if pd.notna(row.get('RPM')) else None,
            n_gear=int(safe_float_conversion(row.get('nGear'), 0)) if pd.notna(row.get('nGear')) else None,
            throttle=safe_float_conversion(row.get('Throttle')) if pd.notna(row.get('Throttle')) else None,
            brake=bool(row.get('Brake', False)) if pd.notna(row.get('Brake')) else None,
            drs=int(safe_float_conversion(row.get('DRS'), 0)) if pd.notna(row.get('DRS')) else None
        )
        telemetry_points.append(point)
    
    return telemetry_points

def calculate_lap_statistics(telemetry_df: pd.DataFrame) -> dict:
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

def normalize_coordinates(telemetry_df: pd.DataFrame):
    """Normalize X,Y coordinates for SVG generation"""
    if 'X' not in telemetry_df.columns or 'Y' not in telemetry_df.columns:
        return telemetry_df, 1.0, 0.0, 0.0
    
    x_coords = telemetry_df['X'].dropna()
    y_coords = telemetry_df['Y'].dropna()
    
    if x_coords.empty or y_coords.empty:
        return telemetry_df, 1.0, 0.0, 0.0
    
    # Calculate bounds
    x_min, x_max = x_coords.min(), x_coords.max()
    y_min, y_max = y_coords.min(), y_coords.max()
    
    # Calculate scale to fit in 800x600 viewport
    x_range = x_max - x_min
    y_range = y_max - y_min
    scale = min(800 / x_range, 600 / y_range) if x_range > 0 and y_range > 0 else 1.0
    
    # Normalize coordinates
    telemetry_df['X_norm'] = (telemetry_df['X'] - x_min) * scale
    telemetry_df['Y_norm'] = (telemetry_df['Y'] - y_min) * scale
    
    return telemetry_df, scale, x_min, y_min

def generate_svg_path(coordinates: np.ndarray) -> str:
    """Generate SVG path data (d attribute) from coordinates"""
    if len(coordinates) == 0:
        return ""
    
    path_parts = [f"M {coordinates[0][0]:.2f} {coordinates[0][1]:.2f}"]
    
    for coord in coordinates[1:]:
        path_parts.append(f"L {coord[0]:.2f} {coord[1]:.2f}")
    
    return " ".join(path_parts)


@router.get("/fastest-lap/{year}/{event}/{session}/{driver}", response_model=FastestLapTelemetryResponse)
async def get_fastest_lap_telemetry(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver: str = Path(..., description="Driver abbreviation (e.g., 'VER', 'HAM')"),
):
    """
    Get detailed telemetry data for a driver's fastest lap in a session.
    
    Returns speed, throttle, brake, RPM, DRS, and gear data for the fastest lap.
    
    - **year**: Season year
    - **event**: Event name or round number
    - **session**: Session type (R=Race, Q=Qualifying, S=Sprint, FP1/2/3=Practice)
    - **driver**: Driver abbreviation
    """
    try:
        # Get session using FastF1
        mapped_event = map_event_identifier(event)
        session_obj = fastf1.get_session(year, mapped_event, session)
        session_obj.load()
        
        # Get driver's fastest lap
        driver_laps = session_obj.laps.pick_drivers(driver.upper())
        
        if driver_laps.empty:
            raise HTTPException(status_code=404, detail=f"No laps found for driver {driver}")
        
        # Filter out invalid laps before finding fastest
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        if valid_laps.empty:
            raise HTTPException(status_code=404, detail=f"No valid laps found for driver {driver}")
        
        # Find the fastest lap
        lap_times = valid_laps['LapTime'].dt.total_seconds()
        fastest_lap_idx = lap_times.idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        
        # Get telemetry for the fastest lap
        lap_telemetry = fastest_lap.get_telemetry()
        if lap_telemetry.empty:
            raise HTTPException(status_code=404, detail=f"No telemetry data available for {driver}'s fastest lap")
        
        # Add distance to telemetry
        lap_telemetry = lap_telemetry.add_distance()
        
        # Process telemetry points
        telemetry_points = process_telemetry_data(lap_telemetry)
        
        # Calculate statistics
        lap_stats = calculate_lap_statistics(lap_telemetry)
        
        response = FastestLapTelemetryResponse(
            driver=driver.upper(),
            lap_number=int(fastest_lap.get('LapNumber', 0)),
            lap_time=safe_timedelta_to_seconds(fastest_lap.get('LapTime')),
            telemetry_points=telemetry_points,
            **lap_stats
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fastest lap telemetry: {str(e)}")

@router.get("/track-dominance/{year}/{event}/{session}", response_model=TrackDominanceResponse)
async def get_track_dominance(
    year: int = Path(..., description="Season year"),
    event: str = Path(..., description="Event name or round number"),
    session: str = Path(..., description="Session type (R, Q, S, FP1, FP2, FP3)"),
    driver1: str = Query(..., description="First driver abbreviation"),
    driver2: str = Query(..., description="Second driver abbreviation"),
    lap1_identifier: str = Query("fastest", description="Lap identifier for driver 1 (fastest or lap number)"),
    lap2_identifier: str = Query("fastest", description="Lap identifier for driver 2 (fastest or lap number)"),
    driver1_color: str = Query("#FF0000", description="Hex color code for driver 1"),
    driver2_color: str = Query("#0000FF", description="Hex color code for driver 2"),
):
    """
    Get track dominance comparison between two drivers with SVG visualization.
    
    Returns track sections showing which driver is faster in each segment,
    along with SVG paths for visualization.
    
    - **driver1**: First driver abbreviation
    - **driver2**: Second driver abbreviation
    - **lap1_identifier**: Lap to use for driver 1 ('fastest' or specific lap number)
    - **lap2_identifier**: Lap to use for driver 2 ('fastest' or specific lap number)
    - **driver1_color**: Hex color code for driver 1 visualization
    - **driver2_color**: Hex color code for driver 2 visualization
    """
    try:
        # Get session using FastF1
        mapped_event = map_event_identifier(event)
        session_obj = fastf1.get_session(year, mapped_event, session)
        session_obj.load(laps=True, telemetry=True, weather=False, messages=False)
        
        # Get laps for both drivers
        laps_driver1 = session_obj.laps.pick_drivers([driver1.upper()])
        laps_driver2 = session_obj.laps.pick_drivers([driver2.upper()])
        
        # Get target lap for driver 1
        if lap1_identifier.lower() == 'fastest':
            valid_laps1 = laps_driver1[laps_driver1['LapTime'].notna()]
            if not valid_laps1.empty:
                lap_times1 = valid_laps1['LapTime'].dt.total_seconds()
                fastest_lap_idx1 = lap_times1.idxmin()
                lap1 = valid_laps1.loc[fastest_lap_idx1]
            else:
                lap1 = None
        else:
            try:
                lap_num = int(lap1_identifier)
                lap1_filtered = laps_driver1[laps_driver1['LapNumber'] == lap_num]
                lap1 = lap1_filtered.iloc[0] if not lap1_filtered.empty else None
            except (ValueError, IndexError):
                lap1 = None
        
        # Get target lap for driver 2
        if lap2_identifier.lower() == 'fastest':
            valid_laps2 = laps_driver2[laps_driver2['LapTime'].notna()]
            if not valid_laps2.empty:
                lap_times2 = valid_laps2['LapTime'].dt.total_seconds()
                fastest_lap_idx2 = lap_times2.idxmin()
                lap2 = valid_laps2.loc[fastest_lap_idx2]
            else:
                lap2 = None
        else:
            try:
                lap_num = int(lap2_identifier)
                lap2_filtered = laps_driver2[laps_driver2['LapNumber'] == lap_num]
                lap2 = lap2_filtered.iloc[0] if not lap2_filtered.empty else None
            except (ValueError, IndexError):
                lap2 = None
        
        # Validate laps
        if lap1 is None or pd.isna(lap1['LapTime']):
            raise HTTPException(status_code=404, detail=f"Lap {lap1_identifier} not available for driver {driver1}")
        if lap2 is None or pd.isna(lap2['LapTime']):
            raise HTTPException(status_code=404, detail=f"Lap {lap2_identifier} not available for driver {driver2}")
        
        # Get telemetry
        tel1 = lap1.get_telemetry().add_distance()
        tel2 = lap2.get_telemetry().add_distance()
        
        # Validate telemetry
        required_cols = ['X', 'Y', 'Distance', 'Time']
        if tel1.empty or not all(col in tel1.columns for col in required_cols):
            raise HTTPException(status_code=404, detail=f"Required telemetry data missing for {driver1}")
        if tel2.empty or not all(col in tel2.columns for col in required_cols):
            raise HTTPException(status_code=404, detail=f"Required telemetry data missing for {driver2}")
        
        # Normalize coordinates and generate base layout
        tel1_norm, scale, offset_x, offset_y = normalize_coordinates(tel1.copy())
        
        circuit_layout_svg = generate_svg_path(tel1_norm[['X_norm', 'Y_norm']].values)
        
        # Segment the track
        num_segments = 20
        total_distance = tel1['Distance'].max()
        segment_length = total_distance / num_segments
        segment_boundaries = np.linspace(0, total_distance, num_segments + 1)
        
        # Compare time per segment
        time_interpolator1 = interp1d(
            tel1['Distance'], 
            tel1['Time'].dt.total_seconds(), 
            bounds_error=False, 
            fill_value="extrapolate"
        )
        time_interpolator2 = interp1d(
            tel2['Distance'], 
            tel2['Time'].dt.total_seconds(), 
            bounds_error=False, 
            fill_value="extrapolate"
        )
        
        track_sections = []
        for i in range(num_segments):
            start_dist = segment_boundaries[i]
            end_dist = segment_boundaries[i+1]
            
            # Get telemetry points within this distance segment
            segment_tel1 = tel1_norm[
                (tel1_norm['Distance'] >= start_dist) & 
                (tel1_norm['Distance'] <= end_dist)
            ]
            
            if segment_tel1.empty:
                continue
            
            # Calculate time taken by each driver for this segment
            time1_start = time_interpolator1(start_dist)
            time1_end = time_interpolator1(end_dist)
            time2_start = time_interpolator2(start_dist)
            time2_end = time_interpolator2(end_dist)
            
            advantage = None
            
            if not (pd.isna(time1_start) or pd.isna(time1_end) or pd.isna(time2_start) or pd.isna(time2_end)):
                delta_time1 = time1_end - time1_start
                delta_time2 = time2_end - time2_start
                # Positive means driver 1 is faster (less time)
                advantage = delta_time2 - delta_time1
            
            # Generate SVG path for this segment
            segment_path_svg = generate_svg_path(segment_tel1[['X_norm', 'Y_norm']].values)
            
            track_sections.append(TrackSection(
                id=f"segment_{i+1}",
                name=f"Segment {i+1}",
                type="sector",
                path=segment_path_svg,
                driver1_advantage=advantage
            ))
        
        response = TrackDominanceResponse(
            sections=track_sections,
            driver1_code=driver1.upper(),
            driver2_code=driver2.upper(),
            driver1_color=driver1_color,
            driver2_color=driver2_color,
            circuit_layout=circuit_layout_svg
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process track dominance: {str(e)}") 