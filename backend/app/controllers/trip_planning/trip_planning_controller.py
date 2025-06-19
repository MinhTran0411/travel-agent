from fastapi import APIRouter, Depends, HTTPException, status
from app.controllers.base_controller import BaseController
from app.security import verify_token
from app.middleware.user_middleware import get_current_user, current_user
from app.models.user import User
from app.models.trip import TripPlanningRequest
from app.services.trip_planning_service import TripPlanningService
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class TripPlanningController(BaseController):
    def __init__(self):
        super().__init__()
        self.trip_planning_service = TripPlanningService()
        
        # Create trip plan endpoint
        self.router.add_api_route(
            "/trip-planning",
            self.create_trip_plan,
            methods=["POST"],
            dependencies=[Depends(verify_token)],
            tags=["Trip Planning"]
        )

    async def create_trip_plan(self, request: TripPlanningRequest, _: User = Depends(get_current_user)) -> Dict:
        """Create a new trip plan based on user preferences."""
        logger.info("Creating new trip plan")
        
        user = current_user.get()
        if not user:
            logger.error("No user found in context")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in context"
            )
        
        try:
            # Call the trip planning service
            trip_plan = await self.trip_planning_service.create_trip_plan(request, user)
            logger.info(f"Successfully created trip plan for user {user.username}")
            return trip_plan
        except Exception as e:
            logger.error(f"Error creating trip plan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create trip plan: {str(e)}"
            )

router = TripPlanningController().router 