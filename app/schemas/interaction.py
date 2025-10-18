import uuid
from pydantic import BaseModel, Field
from app.models.interaction import InteractionType

class InteractionBase(BaseModel):
    product_id: uuid.UUID
    interaction_type: InteractionType

class InteractionCreate(InteractionBase):
    pass

class InteractionRead(InteractionBase):
    user_id: uuid.UUID

    class Config:
        orm_mode = True