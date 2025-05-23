from fastapi import APIRouter
from app.api.v1.endpoints import schedule, drivers, constructors, results, telemetry

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    schedule.router, 
    prefix="/schedule", 
    tags=["schedule"]
)

api_router.include_router(
    drivers.router, 
    prefix="/drivers", 
    tags=["drivers"]
)

api_router.include_router(
    constructors.router, 
    prefix="/constructors", 
    tags=["constructors"]
)

api_router.include_router(
    results.router, 
    prefix="/results", 
    tags=["results"]
)

api_router.include_router(
    telemetry.router, 
    prefix="/telemetry", 
    tags=["telemetry"]
) 