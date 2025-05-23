from typing import List, Optional
from pydantic import BaseModel

class RaceResultResponse(BaseModel):
    season: int
    round: int
    race_name: str
    circuit_name: str
    race_date: Optional[str] = None
    position: Optional[int] = None
    position_text: str
    points: float
    driver_id: str
    driver_code: Optional[str] = None
    driver_number: Optional[int] = None
    given_name: str
    family_name: str
    constructor_id: str
    constructor_name: str
    grid_position: Optional[int] = None
    laps_completed: Optional[int] = None
    status: str
    fastest_lap_rank: Optional[int] = None
    fastest_lap_time: Optional[str] = None

    class Config:
        from_attributes = True

class QualifyingResultResponse(BaseModel):
    season: int
    round: int
    race_name: str
    circuit_name: str
    race_date: Optional[str] = None
    position: int
    driver_id: str
    driver_code: Optional[str] = None
    driver_number: Optional[int] = None
    given_name: str
    family_name: str
    constructor_id: str
    constructor_name: str
    q1_time: Optional[str] = None
    q2_time: Optional[str] = None
    q3_time: Optional[str] = None

    class Config:
        from_attributes = True

class SprintResultResponse(BaseModel):
    season: int
    round: int
    race_name: str
    circuit_name: str
    race_date: Optional[str] = None
    position: Optional[int] = None
    position_text: str
    points: float
    driver_id: str
    driver_code: Optional[str] = None
    driver_number: Optional[int] = None
    given_name: str
    family_name: str
    constructor_id: str
    constructor_name: str
    grid_position: Optional[int] = None
    laps_completed: Optional[int] = None
    status: str

    class Config:
        from_attributes = True

class SessionResultResponse(BaseModel):
    position: Optional[int] = None
    driver_number: Optional[int] = None
    driver_abbreviation: Optional[str] = None
    driver_name: str
    team_name: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    points: Optional[float] = None

    class Config:
        from_attributes = True

class FullSessionResultsResponse(BaseModel):
    session_info: dict
    results: List[SessionResultResponse]

    class Config:
        from_attributes = True 