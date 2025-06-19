from pydantic import BaseModel
from datetime import datetime

class Accommodation(BaseModel):
    type: str
    location: str
    checkin: datetime
    checkout: datetime
    guests: int 