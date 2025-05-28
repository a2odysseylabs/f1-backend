from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class TelemetryPoint(BaseModel):
    """Individual telemetry data point"""
    time: float  # Session time in seconds
    distance: Optional[float] = None  # Distance along the track in meters
    speed: Optional[float] = None  # Speed in km/h
    rpm: Optional[int] = None  # Engine RPM
    n_gear: Optional[int] = None  # Current gear
    throttle: Optional[float] = None  # Throttle position (0-100%)
    brake: Optional[bool] = None  # Brake status (True/False)
    drs: Optional[int] = None  # DRS status (0=Closed, 1=Open)
    
    class Config:
        from_attributes = True

class FastestLapTelemetryResponse(BaseModel):
    """Fastest lap telemetry data for a driver"""
    driver: str
    lap_number: int
    lap_time: Optional[float] = None  # Lap time in seconds
    telemetry_points: List[TelemetryPoint]
    
    # Lap summary statistics
    max_speed: Optional[float] = None
    avg_speed: Optional[float] = None
    max_rpm: Optional[int] = None
    avg_rpm: Optional[float] = None
    throttle_percentage: Optional[float] = None
    brake_percentage: Optional[float] = None
    drs_percentage: Optional[float] = None
    gear_changes: Optional[int] = None
    
    class Config:
        from_attributes = True

class TrackSection(BaseModel):
    """Track section for dominance analysis"""
    id: str
    name: str
    type: str
    path: str  # SVG path
    driver1_advantage: Optional[float] = None  # Time advantage in seconds
    
    class Config:
        from_attributes = True

class TrackDominanceResponse(BaseModel):
    """Track dominance comparison between drivers"""
    sections: List[TrackSection]
    driver1_code: str
    driver2_code: str
    driver1_color: str  # Hex color for driver 1
    driver2_color: str  # Hex color for driver 2
    circuit_layout: str  # SVG path for full circuit
    
    class Config:
        from_attributes = True 