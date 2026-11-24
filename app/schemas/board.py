from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BoardCreate(BaseModel):
    title:str


class BoardOut(BaseModel):
    id:int
    title:str
    owner_id:int 
    created_at:datetime
    model_config = ConfigDict(from_attributes=True)  