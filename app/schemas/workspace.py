from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
