from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr

# No "developer" here — workspace membership is admin/manager only.
WorkspaceRole = Literal["admin", "manager"]


class WorkspaceMemberCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole


class WorkspaceMemberRoleUpdate(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberOut(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
