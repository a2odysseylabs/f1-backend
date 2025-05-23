from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ScheduleResponse(BaseModel):
    round_number: Optional[int] = None
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    event_format: Optional[str] = None
    session1_date: Optional[str] = None
    session2_date: Optional[str] = None
    session3_date: Optional[str] = None
    session4_date: Optional[str] = None
    session5_date: Optional[str] = None
    f1_api_support: Optional[bool] = False
    location: Optional[str] = None
    country: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SessionInfo(BaseModel):
    session_name: str
    session_date: str

class EventResponse(BaseModel):
    round_number: Optional[int] = None
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    event_format: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    f1_api_support: Optional[bool] = False
    sessions: List[SessionInfo] = []

    class Config:
        from_attributes = True 