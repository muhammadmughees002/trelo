from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ListCreate(BaseModel):
    title: str
    board_id: int


class ListOut(BaseModel):
    id: int
    title: str
    board_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
