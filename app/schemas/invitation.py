from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr


class WorkspaceInvitationCreate(BaseModel):
    email: EmailStr
    role: Literal["admin", "manager"]


class BoardInvitationCreate(BaseModel):
    email: EmailStr
    role: Literal["admin", "manager", "developer"]


class WorkspaceInvitationOut(BaseModel):
    id: int
    workspace_id: int
    invited_email: str
    role: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BoardInvitationOut(BaseModel):
    id: int
    board_id: int
    invited_email: str
    role: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MyInvitationOut(BaseModel):
    """One combined shape for 'invitations addressed to me', whether they
    target a workspace or a board. `kind` tells the client which accept/
    decline endpoint to call."""
    id: int
    kind: Literal["workspace", "board"]
    target_id: int
    target_name: str
    role: str
    created_at: datetime
