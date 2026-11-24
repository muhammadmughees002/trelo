from datetime import datetime
from pydantic import BaseModel, EmailStr , ConfigDict



class UserCreate(BaseModel):
   email:EmailStr 
   password:str

class UserOut(BaseModel):
   id:int
   email:EmailStr
   full_name: str | None
   bio: str | None
   avatar_url: str | None
   created_at:datetime
   model_config = ConfigDict(from_attributes=True)

class Userlogin(BaseModel):
   email:EmailStr
   password:str


class Token(BaseModel):
   access_token:str
   token_type:str


class UserProfileOut(BaseModel):
    """A view of someone ELSE's profile, after the shared-board +
    hierarchy visibility check has already passed. Intentionally omits
    `id`/`created_at` — the viewer doesn't need the account's internal id,
    just the human-facing fields."""
    email: EmailStr
    full_name: str | None
    bio: str | None
    avatar_url: str | None
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Self-edit only. Deliberately excludes email/password — those are
    a separate, more sensitive flow and out of scope here."""
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class DeveloperEmailUpdate(BaseModel):
    """Used only by a Manager/Admin changing a Developer's email on a
    shared board. See the security note in routers/profile.py before
    reusing this anywhere else."""
    email: EmailStr