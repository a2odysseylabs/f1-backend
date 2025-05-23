from typing import List, Optional
from pydantic import BaseModel

class DriverResponse(BaseModel):
    driver_id: str
    driver_number: Optional[int] = None
    driver_code: Optional[str] = None
    given_name: str
    family_name: str
    date_of_birth: Optional[str] = None
    nationality: str
    driver_url: Optional[str] = None

    class Config:
        from_attributes = True

class DriverSessionResponse(BaseModel):
    driver_abbreviation: str
    driver_number: Optional[int] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    team_name: Optional[str] = None
    team_color: Optional[str] = None

    class Config:
        from_attributes = True

class DriverStandingsResponse(BaseModel):
    position: int
    points: float
    wins: int
    driver_id: str
    driver_code: Optional[str] = None
    given_name: str
    family_name: str
    nationality: str

    class Config:
        from_attributes = True 