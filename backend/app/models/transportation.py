from pydantic import BaseModel
from datetime import datetime

class Transportation(BaseModel):
    type: str
    departureLocation: str
    arrivalLocation: str
    departureTime: datetime
    arrivalTime: datetime
    service_class: str
    passengers: int 