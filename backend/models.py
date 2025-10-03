from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: UUID
    email: EmailStr

class FlowBase(BaseModel):
    instruction: str
    hourInDay: int
    minuteInDay: int
    occurrences: Optional[str] = "dayToDay"

class FlowCreate(FlowBase):
    pass

class Flow(FlowBase):
    id: int
    user_id: UUID

class ReceiverBase(BaseModel):
    email: EmailStr
    name: str
    active: Optional[bool] = True
    flow_id: int

class ReceiverCreate(ReceiverBase):
    pass

class Receiver(ReceiverBase):
    id: int
