import uuid
from pydantic import BaseModel, Field
from app.models.interaction import InteractionType
from app.schemas.product import ProductFeedItemSchema


class InteractionBase(BaseModel):
    product_id: uuid.UUID
    interaction_type: InteractionType

class InteractionCreate(InteractionBase):
    pass

class InteractionRead(InteractionBase):
    user_id: uuid.UUID

    class Config:
        orm_mode = True


class InteractionWithProduct(BaseModel):
    interaction_type: InteractionType
    product: ProductFeedItemSchema

    class Config:
        orm_mode = True