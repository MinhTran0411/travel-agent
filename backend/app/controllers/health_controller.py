from fastapi import APIRouter
from app.controllers.base_controller import BaseController

router = APIRouter(prefix="/health", tags=["Health"])

class HealthController(BaseController):
    def __init__(self):
        super().__init__()
        self.router = router
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/")
        async def health_check():
            return {"status": "healthy"}

# Initialize the controller
health_controller = HealthController() 