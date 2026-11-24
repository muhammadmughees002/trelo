from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr

Role = Literal["admin", "manager", "developer"]


class BoardMemberCreate(BaseModel):
    email: EmailStr
    role: Role


class BoardMemberRoleUpdate(BaseModel):
    role: Role


class BoardMemberOut(BaseModel):
    id: int
    board_id: int
    user_id: int
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
