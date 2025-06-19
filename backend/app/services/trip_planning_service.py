from typing import Dict, Any
import httpx
from datetime import datetime
from bson import ObjectId
from app.config import get_settings
from app.models.trip_plan import TripPlan
from app.models.trip import TripPlanningRequest, TripPlanResponseDTO, SpanResponseDTO
from app.models.span import Span, ActivityTiming, ActivityWithTiming
from app.models.activity import Activity
from app.models.transportation import Transportation
from app.models.accommodation import Accommodation
from app.models.user import User
from app.repositories.trip_repository import TripRepository
from app.helpers.mongo_serializer import prepare_mongo_response
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class TripPlanningService:
    def __init__(self):
        self.settings = get_settings()
        self.orchestration_host = self.settings.orchestration_host
        self.trip_repository = TripRepository()
        # Set default timeout to 5 minutes (300 seconds)
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    async def create_trip_plan(self, request: TripPlanningRequest, user: User) -> Dict[str, Any]:
        """Create a new trip plan based on user preferences."""
        try:
            # Prepare request data for orchestration service
            request_data = {
                "from_location": request.from_location,
                "destination": request.destination,
                "fix_city": request.fix_city,
                "fix_country": request.fix_country,
                "destination_city": request.destination_city,
                "destination_country": request.destination_country,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "budget": request.budget,
                "physical_constraints": [constraint.value for constraint in request.physical_constraints],
                "language_preference": request.language_preference.value,
                "trip_purpose": request.trip_purpose.value,
                "interests": [interest.value for interest in request.interests],
                "pace": request.pace.value,
                "additional_notes": request.additional_notes
            }

            # Call orchestration service with timeout
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Calling orchestration service for trip planning...")
                response = await client.post(
                    f"{self.orchestration_host}/api/v1/plan-trip",
                    json=request_data
                )
                response.raise_for_status()
                trip_data = response.json()
                logger.info("Received response from orchestration service")

            # Process the response data
            trip_plan = await self._process_trip_data(trip_data, user.id)
            
            # Save to database using repository
            trip_id = await self.trip_repository.save_trip(trip_plan)
            
            # Update the trip plan with the generated ID
            trip_plan.tripId = trip_id
            
            # Update user's tripPlanIds
            await self._update_user_trip_plans(user.id, trip_id)
            
            # Convert to response DTO
            response_dto = await self._create_response_dto(trip_plan)
            
            return prepare_mongo_response(response_dto.model_dump(by_alias=True))

        except httpx.TimeoutException as e:
            logger.error(f"Timeout while calling orchestration service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The trip planning service is taking longer than expected. Please try again later."
            )
        except httpx.HTTPError as e:
            logger.error(f"Error calling orchestration service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with trip planning service"
            )
        except Exception as e:
            logger.error(f"Error processing trip plan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while planning your trip"
            )

    async def _process_trip_data(self, data: Dict[str, Any], user_id: ObjectId) -> TripPlan:
        """Process the raw trip data into a TripPlan object."""
        # Convert spans data
        processed_spans = []
        for span_data in data["spans"]:
            # Save activities and get their IDs with timing
            activities = []
            for activity_data in span_data["activities"]:
                activity = Activity(
                    activityId=activity_data["activityId"],
                    name=activity_data["name"],
                    description=activity_data["description"],
                    location=activity_data["location"],
                    category=activity_data["category"]
                )
                # Save activity to its collection
                await self.trip_repository.save_activity_metadata(activity)
                
                # Create activity timing object
                activity_timing = ActivityTiming(
                    activityId=activity_data["activityId"],
                    startTime=datetime.fromisoformat(activity_data["startTime"].replace("Z", "+00:00")),
                    endTime=datetime.fromisoformat(activity_data["endTime"].replace("Z", "+00:00"))
                )
                activities.append(activity_timing)

            # Process transportation
            transportation = [
                Transportation(
                    type=t["type"],
                    departureLocation=t["departureLocation"],
                    arrivalLocation=t["arrivalLocation"],
                    departureTime=datetime.fromisoformat(t["departureTime"].replace("Z", "+00:00")),
                    arrivalTime=datetime.fromisoformat(t["arrivalTime"].replace("Z", "+00:00")),
                    service_class=t["service_class"],
                    passengers=t["passengers"]
                )
                for t in span_data["transportation"]
            ]

            # Process accommodation
            accommodation = [
                Accommodation(
                    type=a["type"],
                    location=a["location"],
                    checkin=datetime.fromisoformat(a["checkin"].replace("Z", "+00:00")),
                    checkout=datetime.fromisoformat(a["checkout"].replace("Z", "+00:00")),
                    guests=a["guests"]
                )
                for a in span_data["accommodation"]
            ]

            # Create Span object with activity timings
            span = Span(
                spanId=span_data["spanId"],
                spanTitle=span_data["spanTitle"],
                spanDescription=span_data["spanDescription"],
                from_location=span_data["from_location"],
                to_location=span_data["to_location"],
                startDate=datetime.fromisoformat(span_data["startDate"].replace("Z", "+00:00")),
                endDate=datetime.fromisoformat(span_data["endDate"].replace("Z", "+00:00")),
                transportation=transportation,
                accommodation=accommodation,
                activities=activities,
                notes=span_data.get("notes")
            )
            processed_spans.append(span)

        # Create TripPlan object without tripId - let MongoDB generate it
        trip_plan = TripPlan(
            userId=user_id,
            title=data["title"],
            from_location=data["from_location"],
            to_location=data["to_location"],
            startDate=datetime.fromisoformat(data["startDate"].replace("Z", "+00:00")),
            endDate=datetime.fromisoformat(data["endDate"].replace("Z", "+00:00")),
            spans=processed_spans
        )

        return trip_plan

    async def _update_user_trip_plans(self, user_id: ObjectId, trip_id: str) -> None:
        """Update user's tripPlanIds with the new trip ID."""
        try:
            await self.trip_repository.update_user_trip_plans(user_id, trip_id)
            logger.info(f"Updated tripPlanIds for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating user's tripPlanIds: {str(e)}")
            raise

    async def _create_response_dto(self, trip_plan: TripPlan) -> TripPlanResponseDTO:
        """Create a response DTO with full activity details."""
        spans_dto = []
        for span in trip_plan.spans:
            # Fetch full activity details
            activities_with_timing = []
            for activity_timing in span.activities:
                activity = await self.trip_repository.get_activity_metadata(activity_timing.activityId)
                if activity:
                    activities_with_timing.append(ActivityWithTiming(
                        activity=activity,
                        startTime=activity_timing.startTime,
                        endTime=activity_timing.endTime
                    ))
            
            # Create span DTO with full activity details
            span_dto = SpanResponseDTO(
                spanId=span.spanId,
                spanTitle=span.spanTitle,
                spanDescription=span.spanDescription,
                from_location=span.from_location,
                to_location=span.to_location,
                startDate=span.startDate,
                endDate=span.endDate,
                transportation=span.transportation,
                accommodation=span.accommodation,
                activities=activities_with_timing,
                notes=span.notes
            )
            spans_dto.append(span_dto)

        # Create and return the full response DTO
        return TripPlanResponseDTO(
            tripId=trip_plan.tripId,
            userId=str(trip_plan.userId),
            title=trip_plan.title,
            from_location=trip_plan.from_location,
            to_location=trip_plan.to_location,
            startDate=trip_plan.startDate,
            endDate=trip_plan.endDate,
            spans=spans_dto
        ) 