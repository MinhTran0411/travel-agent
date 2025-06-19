from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from app.models.trip_plan import TripPlan
from app.models.activity import Activity
from app.config import get_settings
from bson import ObjectId

settings = get_settings()

class TripRepository:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.database_name]
        self.trips = self.db.trips
        self.activities = self.db.activities
        self.users = self.db.users

    async def save_trip(self, trip: TripPlan) -> str:
        """Save trip plan and return the generated MongoDB ID."""
        # Convert to dict and remove tripId if it exists
        trip_dict = trip.model_dump(by_alias=True)
        trip_dict.pop('_id', None)  # Remove _id if it exists
        
        # Insert the document and get the result
        result = await self.trips.insert_one(trip_dict)
        
        # Return the generated _id as string
        return str(result.inserted_id)

    async def get_trip(self, trip_id: str) -> Optional[TripPlan]:
        trip_data = await self.trips.find_one({"_id": trip_id})
        if trip_data:
            return TripPlan(**trip_data)
        return None

    async def save_activity_metadata(self, activity: Activity) -> str:
        """Save activity metadata, updating only changed fields."""
        # Get existing activity if any
        existing = await self.activities.find_one({"activityId": activity.activityId})
        
        if existing:
            # Update only changed fields
            update_data = {}
            activity_dict = activity.model_dump()
            for key, value in activity_dict.items():
                if key not in existing or existing[key] != value:
                    update_data[key] = value
            
            if update_data:
                await self.activities.update_one(
                    {"activityId": activity.activityId},
                    {"$set": update_data}
                )
        else:
            # Insert new activity
            await self.activities.insert_one(activity.model_dump())
            
        return activity.activityId

    async def get_activity_metadata(self, activity_id: str) -> Optional[Activity]:
        activity_data = await self.activities.find_one({"activityId": activity_id})
        if activity_data:
            return Activity(**activity_data)
        return None

    async def get_activities_by_ids(self, activity_ids: List[str]) -> List[Activity]:
        cursor = self.activities.find({"activityId": {"$in": activity_ids}})
        activities = []
        async for doc in cursor:
            activities.append(Activity(**doc))
        return activities

    async def update_user_trip_plans(self, user_id: ObjectId, trip_id: str) -> None:
        """Add a trip ID to user's tripPlanIds array."""
        await self.users.update_one(
            {"_id": user_id},
            {"$addToSet": {"tripPlanIds": trip_id}}  # $addToSet ensures no duplicates
        ) 