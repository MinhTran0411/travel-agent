from fastapi import APIRouter, Depends, HTTPException, status
from app.controllers.base_controller import BaseController
from app.security import verify_token, require_admin, require_user
from app.middleware.user_middleware import get_current_user, current_user
from typing import Dict
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class MockController(BaseController):
    def __init__(self):
        super().__init__()
        # Public endpoint - no auth required
        self.router.add_api_route(
            "/mock/public",
            self.public_endpoint,
            methods=["GET"],
            tags=["Mock"]
        )
        
        # Protected endpoint - requires valid token
        self.router.add_api_route(
            "/mock/protected",
            self.protected_endpoint,
            methods=["GET"],
            dependencies=[Depends(verify_token)],
            tags=["Mock"]
        )
        
        # Admin endpoint - requires admin role
        self.router.add_api_route(
            "/mock/admin",
            self.admin_endpoint,
            methods=["GET"],
            dependencies=[Depends(verify_token)],
            tags=["Mock"]
        )

    async def public_endpoint(self) -> Dict:
        logger.info("Public endpoint: Returning public endpoint response")
        return {
            "message": "This is a public endpoint",
            "status": "success"
        }

    async def protected_endpoint(self, _: User = Depends(get_current_user)) -> Dict:
        """Protected endpoint that verifies current_user context after dependency ensures it's set."""
        logger.info("Protected endpoint: Verifying current_user context")
        
        user = current_user.get()
        if not user:
            logger.error("Protected endpoint: No user found in context despite dependency")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in context"
            )
        
        logger.info(f"Protected endpoint: Verified user in context: {user.username}")
        return {
            "message": "This is a protected endpoint",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "tripPlanIds": user.tripPlanIds,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }

    @require_admin
    async def admin_endpoint(self, token_data: dict = Depends(verify_token)) -> Dict:
        logger.info("Admin endpoint: Returning admin endpoint response")
        return {
            "message": "This is an admin endpoint",
            "status": "success",
            "user": token_data.get("sub", "unknown"),
            "roles": token_data.get("realm_access", {}).get("roles", [])
        }

router = MockController().router 