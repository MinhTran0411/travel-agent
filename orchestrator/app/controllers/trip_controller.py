from fastapi import APIRouter, HTTPException, Query
from typing import Dict
from app.models.trip import TripPreferences, TripPlan
from app.services.trip_service import TripService
from app.services.activity_processing_service import ActivityProcessingService

router = APIRouter()
trip_service = TripService()
activity_processor = ActivityProcessingService()

@router.post("/plan-trip", response_model=TripPlan)
async def plan_trip(preferences: TripPreferences):
    """
    Create a comprehensive trip plan with activity deduplication and ID assignment.
    
    The service will:
    1. Generate trip plan using LLM
    2. Process activities through normalization and deduplication
    3. Assign consistent activity IDs using semantic matching
    4. Return enhanced trip plan with activityId fields
    """
    try:
        trip_plan = await trip_service.plan_trip(preferences)
        return trip_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-stats")
async def get_activity_stats():
    """Get statistics about stored activities in the processing database."""
    try:
        stats = activity_processor.get_activity_stats()
        return {
            "message": "Activity processing statistics",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-activities")
async def process_activities_endpoint(trip_plan_json: Dict):
    """
    Test endpoint to process activities in a trip plan JSON.
    
    This endpoint allows testing the activity processing pipeline independently.
    """
    try:
        processed_plan = activity_processor.process_trip_plan(trip_plan_json)
        return {
            "message": "Activities processed successfully",
            "data": processed_plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup-activities/{days_old}")
async def cleanup_old_activities(days_old: int):
    """Remove activities not used in the last N days."""
    try:
        deleted_count = activity_processor.cleanup_old_activities(days_old)
        return {
            "message": f"Cleaned up old activities",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mock-plan-trip")
async def mock_plan_trip(preferences: TripPreferences):
    """
    Mock endpoint that returns a predefined trip plan for testing.
    This endpoint bypasses the LLM call and returns a fixed response.
    """
    mock_response = {
        "tripId": "trip_12345",
        "title": "Exploration of Japan",
        "from_location": "SGN",
        "to_location": "SGN",
        "startDate": "2025-06-30T00:00:00Z",
        "endDate": "2025-07-07T00:00:00Z",
        "spans": [
            {
                "spanId": "span_1",
                "spanTitle": "Exploration of Tokyo",
                "spanDescription": "Experience the vibrancy of Tokyo with its rich culture and shopping spots",
                "from_location": "SGN",
                "to_location": "TYO",
                "startDate": "2025-06-30T00:00:00",
                "endDate": "2025-07-02T00:00:00",
                "transportation": [
                    {
                        "type": "flight",
                        "departureLocation": "SGN",
                        "arrivalLocation": "TYO",
                        "departureTime": "2025-06-30T08:00:00Z",
                        "arrivalTime": "2025-06-30T16:00:00Z",
                        "service_class": "economy",
                        "passengers": 1
                    }
                ],
                "accommodation": [
                    {
                        "type": "hotel",
                        "location": "TYO",
                        "checkin": "2025-06-30T18:00:00Z",
                        "checkout": "2025-07-02T11:00:00Z",
                        "guests": 1
                    }
                ],
                "activities": [
                    {
                        "name": "Tokyo Skytree",
                        "description": "Visit the tallest tower in the world and enjoy the panoramic view of Tokyo",
                        "location": "TYO",
                        "startTime": "2025-06-30T18:00:00Z",
                        "endTime": "2025-06-30T21:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Tsukiji Outer Market",
                        "description": "Explore the largest wholesale fish and seafood market in the world",
                        "location": "TYO",
                        "startTime": "2025-07-01T09:00:00Z",
                        "endTime": "2025-07-01T12:00:00Z",
                        "participants": 1,
                        "category": "food",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Mori Art Museum",
                        "description": "Visit this contemporary art museum located in the Roppongi district",
                        "location": "TYO",
                        "startTime": "2025-07-01T14:00:00Z",
                        "endTime": "2025-07-01T17:00:00Z",
                        "participants": 1,
                        "category": "museum",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Ginza Shopping District",
                        "description": "Enjoy shopping at Tokyo's most famous upscale shopping district",
                        "location": "TYO",
                        "startTime": "2025-07-02T09:00:00Z",
                        "endTime": "2025-07-02T12:00:00Z",
                        "participants": 1,
                        "category": "shopping",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Ueno Park",
                        "description": "Explore this spacious public park, home to several major museums",
                        "location": "TYO",
                        "startTime": "2025-07-02T14:00:00Z",
                        "endTime": "2025-07-02T17:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    }
                ],
                "notes": "Remember to bring a camera for photography opportunities"
            },
            {
                "spanId": "span_2",
                "spanTitle": "Exploration of Kyoto",
                "spanDescription": "Experience the traditional side of Japan in the city of Kyoto",
                "from_location": "TYO",
                "to_location": "KIX",
                "startDate": "2025-07-03T00:00:00",
                "endDate": "2025-07-06T00:00:00",
                "transportation": [
                    {
                        "type": "train",
                        "departureLocation": "TYO",
                        "arrivalLocation": "KIX",
                        "departureTime": "2025-07-03T08:00:00Z",
                        "arrivalTime": "2025-07-03T14:00:00Z",
                        "service_class": "economy",
                        "passengers": 1
                    }
                ],
                "accommodation": [
                    {
                        "type": "hotel",
                        "location": "KIX",
                        "checkin": "2025-07-03T16:00:00Z",
                        "checkout": "2025-07-06T11:00:00Z",
                        "guests": 1
                    }
                ],
                "activities": [
                    {
                        "name": "Fushimi Inari Shrine",
                        "description": "Visit one of the most important Shinto shrines in southern Kyoto",
                        "location": "KIX",
                        "startTime": "2025-07-03T16:00:00Z",
                        "endTime": "2025-07-03T19:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Arashiyama Bamboo Grove",
                        "description": "Stroll through one of Kyoto's top sights and capture beautiful photos",
                        "location": "KIX",
                        "startTime": "2025-07-04T09:00:00Z",
                        "endTime": "2025-07-04T12:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Kyoto Imperial Palace",
                        "description": "Explore the former residence of the Imperial family, surrounded by stunning gardens",
                        "location": "KIX",
                        "startTime": "2025-07-04T14:00:00Z",
                        "endTime": "2025-07-04T17:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Nishiki Market",
                        "description": "Experience shopping at a traditional Japanese market",
                        "location": "KIX",
                        "startTime": "2025-07-05T09:00:00Z",
                        "endTime": "2025-07-05T12:00:00Z",
                        "participants": 1,
                        "category": "shopping",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Kinkaku-ji Temple",
                        "description": "Visit the Zen Buddhist temple, one of the most popular buildings in Japan",
                        "location": "KIX",
                        "startTime": "2025-07-05T14:00:00Z",
                        "endTime": "2025-07-05T17:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    },
                    {
                        "name": "Gion District",
                        "description": "Explore Kyoto's most famous geisha district and enjoy its quaint charm",
                        "location": "KIX",
                        "startTime": "2025-07-06T09:00:00Z",
                        "endTime": "2025-07-06T12:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    }
                ],
                "notes": "Remember to wear comfortable shoes for walking tours"
            },
            {
                "spanId": "span_3",
                "spanTitle": "Return to Ho Chi Minh City, Vietnam",
                "spanDescription": "Final day and return journey",
                "from_location": "KIX",
                "to_location": "SGN",
                "startDate": "2025-07-07T00:00:00",
                "endDate": "2025-07-07T00:00:00",
                "transportation": [
                    {
                        "type": "flight",
                        "departureLocation": "KIX",
                        "arrivalLocation": "SGN",
                        "departureTime": "2025-07-07T15:00:00Z",
                        "arrivalTime": "2025-07-07T21:00:00Z",
                        "service_class": "economy",
                        "passengers": 1
                    }
                ],
                "accommodation": [],
                "activities": [
                    {
                        "name": "Osaka Castle",
                        "description": "Visit the historical castle in the heart of Osaka before departure",
                        "location": "KIX",
                        "startTime": "2025-07-07T09:00:00Z",
                        "endTime": "2025-07-07T12:00:00Z",
                        "participants": 1,
                        "category": "tour",
                        "activityId": "activity_a8f5d81d53e9624d"
                    }
                ],
                "notes": "Check all belongings before leaving for the airport"
            }
        ]
    }
    
    # Convert directly to TripPlan object
    return TripPlan(**mock_response)
 