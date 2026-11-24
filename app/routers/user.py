from fastapi import APIRouter,Depends, HTTPException,status
from app.schemas.user import UserCreate ,UserOut ,Userlogin,Token
from app.core.dependencies import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password,create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register",response_model=UserOut,status_code=status.HTTP_201_CREATED)
def create_user(user_data:UserCreate,db:Session=Depends(get_db)):
    found=db.query(User).filter(User.email == user_data.email).first()
    if found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password=hash_password(user_data.password)

    new_user=User(
        email=user_data.email,
        hashed_password=hashed_password,  
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login",response_model=Token,status_code=status.HTTP_200_OK)
def login(user_data:Userlogin,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not verify_password(user_data.password,user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token=create_access_token(data={"sub":str(user.id)})
    return{"access_token": access_token,"token_type": "bearer"}
    
   