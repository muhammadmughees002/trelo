from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BoardCreate(BaseModel):
    title: str
    workspace_id: int


class BoardOut(BaseModel):
    id: int
    title: str
    owner_id: int
    workspace_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
