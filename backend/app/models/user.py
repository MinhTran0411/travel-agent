from typing import List
from pydantic import Field
from app.models.base import MongoBaseModel

class User(MongoBaseModel):
    username: str = Field(unique=True, index=True)
    tripPlanIds: List[str] = Field(default_factory=list)

    class Config:
        collection = "users"
        indexes = [
            {"key": [("username", 1)], "unique": True}
        ] 