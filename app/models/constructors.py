from typing import Optional
from pydantic import BaseModel

class ConstructorResponse(BaseModel):
    constructor_id: str
    constructor_name: str
    nationality: str
    constructor_url: Optional[str] = None

    class Config:
        from_attributes = True

class ConstructorStandingsResponse(BaseModel):
    position: int
    points: float
    wins: int
    constructor_id: str
    constructor_name: str
    nationality: str

    class Config:
        from_attributes = True 