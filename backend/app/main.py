from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.health_controller import router as health_router
from app.controllers.mock_controller import router as mock_router
from app.controllers.trip_planning.trip_planning_controller import router as trip_planning_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Travel Agent API",
    description="API for travel planning and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers with prefixes
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(mock_router, prefix="/api/v1", tags=["Mock"])
app.include_router(trip_planning_router, prefix="/api/v1", tags=["Trip Planning"]) 