from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class CardCreate(BaseModel):
    title: str
    description: str | None = None
    list_id: int
    assignee_email: EmailStr | None = None


class CardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_email: EmailStr | None = None
    # Explicit flag to clear an existing assignment, since omitting
    # assignee_email just means "leave it unchanged," not "remove it."
    unassign: bool = False


class CardOut(BaseModel):
    id: int
    title: str
    description: str | None
    list_id: int
    assigned_user_id: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
