from datetime import datetime
from pydantic import BaseModel, EmailStr , ConfigDict



class UserCreate(BaseModel):
   email:EmailStr
   password:str

class UserOut(BaseModel):
   id:int
   email:EmailStr
   created_at:datetime
   model_config = ConfigDict(from_attributes=True)

class Userlogin(BaseModel):
   email:EmailStr
   password:str


class Token(BaseModel):
   access_token:str
   token_type:str
