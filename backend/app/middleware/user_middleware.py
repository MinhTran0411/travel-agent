from contextvars import ContextVar
from fastapi import Request, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import User
from app.config import get_settings
from app.security import verify_token
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Create a context variable to store the current user
current_user: ContextVar[User] = ContextVar("current_user", default=None)

async def get_current_user(token_data: dict = Depends(verify_token)) -> User:
    """Dependency to get or create the current user."""
    logger.info("get_current_user: Processing request")
    
    if not token_data or "email" not in token_data:
        logger.error("get_current_user: No token data or email found")
        return None

    try:
        # Initialize MongoDB client
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        logger.info(f"get_current_user: Looking up user with username: {token_data['email']}")
        
        # Create new user data
        new_user = User(
            username=token_data['email'],
            tripPlanIds=[]
        )
        
        # Use find_one_and_update with upsert to either find existing user or create new one
        user_data = await db.users.find_one_and_update(
            {"username": token_data["email"]},
            {"$setOnInsert": new_user.model_dump(exclude={'id'}, by_alias=True)},
            upsert=True,
            return_document=True
        )
        
        user = User(**user_data)
        logger.info(f"get_current_user: User {'created' if user_data.get('_id') else 'found'}: {user.username}")

        # Store user in context
        current_user.set(user)
        logger.info(f"get_current_user: User set in context: {user.username}")
        return user

    except Exception as e:
        logger.error(f"get_current_user: Error processing user: {str(e)}")
        return None 