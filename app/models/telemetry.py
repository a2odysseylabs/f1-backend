from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class TelemetryPoint(BaseModel):
    """Individual telemetry data point"""
    time: float  # Session time in seconds
    distance: Optional[float] = None  # Distance along the track in meters
    
    # Position data
    x: Optional[float] = None  # World position X coordinate
    y: Optional[float] = None  # World position Y coordinate
    z: Optional[float] = None  # World position Z coordinate
    
    # Basic telemetry
    speed: Optional[float] = None  # Speed in km/h
    rpm: Optional[int] = None  # Engine RPM
    n_gear: Optional[int] = None  # Current gear (0=Neutral, -1=Reverse, 1-8=Forward gears)
    throttle: Optional[float] = None  # Throttle position (0-100%)
    brake: Optional[bool] = None  # Brake status (True/False)
    drs: Optional[int] = None  # DRS status (0=Closed, 1=Open)
    
    # Advanced telemetry
    steering: Optional[float] = None  # Steering wheel angle in degrees
    
    class Config:
        from_attributes = True

class LapTelemetryResponse(BaseModel):
    """Telemetry data for a complete lap"""
    driver: str
    lap_number: int
    lap_time: Optional[float] = None  # Lap time in seconds
    is_accurate: bool = True  # Whether the lap is accurate (no invalid sectors)
    telemetry_points: List[TelemetryPoint]
    
    # Lap summary statistics
    max_speed: Optional[float] = None
    avg_speed: Optional[float] = None
    max_rpm: Optional[int] = None
    avg_rpm: Optional[float] = None
    throttle_percentage: Optional[float] = None  # Average throttle usage
    brake_percentage: Optional[float] = None  # Percentage of lap spent braking
    drs_percentage: Optional[float] = None  # Percentage of lap with DRS open
    gear_changes: Optional[int] = None  # Number of gear changes in the lap
    
    class Config:
        from_attributes = True

class SessionTelemetryResponse(BaseModel):
    """Telemetry data for all drivers in a session"""
    session_info: Dict[str, Any]
    drivers: List[str]
    laps: List[LapTelemetryResponse]
    
    class Config:
        from_attributes = True

class DriverComparisonResponse(BaseModel):
    """Telemetry comparison between two drivers"""
    driver_1: str
    driver_2: str
    lap_1: LapTelemetryResponse
    lap_2: LapTelemetryResponse
    comparison_stats: Dict[str, Any]
    
    class Config:
        from_attributes = True

class TelemetrySummaryResponse(BaseModel):
    """Summary statistics for driver telemetry"""
    driver: str
    session_type: str
    total_laps: int
    fastest_lap: Optional[LapTelemetryResponse] = None
    
    # Session statistics
    session_max_speed: Optional[float] = None
    session_avg_speed: Optional[float] = None
    session_max_rpm: Optional[int] = None
    total_distance: Optional[float] = None
    
    # Driving style metrics
    avg_throttle_usage: Optional[float] = None
    avg_brake_usage: Optional[float] = None
    aggressive_braking_count: Optional[int] = None  # Sudden brake applications
    drs_usage_percentage: Optional[float] = None
    gear_change_frequency: Optional[float] = None  # Changes per lap
    
    class Config:
        from_attributes = True

class TrackDataResponse(BaseModel):
    """Track-specific telemetry data and statistics"""
    track_name: str
    track_length: Optional[float] = None  # Track length in meters
    corner_count: Optional[int] = None
    
    # Track characteristics from telemetry
    speed_zones: List[Dict[str, Any]] = []  # High/medium/low speed zones
    braking_zones: List[Dict[str, Any]] = []  # Major braking points
    drs_zones: List[Dict[str, Any]] = []  # DRS activation zones
    
    class Config:
        from_attributes = True

class StintTelemetryResponse(BaseModel):
    """Telemetry data for a specific stint (set of consecutive laps)"""
    driver: str
    stint_number: int
    start_lap: int
    end_lap: int
    tire_compound: Optional[str] = None
    tire_age: Optional[int] = None  # Laps on this tire set
    
    # Stint performance metrics
    stint_laps: List[LapTelemetryResponse]
    avg_lap_time: Optional[float] = None
    fastest_lap_time: Optional[float] = None
    tire_degradation: Optional[float] = None  # Time loss per lap
    
    # Stint telemetry summary
    avg_speed: Optional[float] = None
    avg_throttle: Optional[float] = None
    avg_brake_usage: Optional[float] = None
    
    class Config:
        from_attributes = True 