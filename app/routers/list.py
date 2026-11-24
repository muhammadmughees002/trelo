from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import get_membership_or_404, get_board_via_list_or_404, MANAGE_ROLES
from app.models.list import List
from app.models.user import User
from app.schemas.list import ListCreate, ListOut

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("/", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(list_data: ListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only admin/manager may create lists on this board.
    get_membership_or_404(db, list_data.board_id, current_user, allowed_roles=MANAGE_ROLES)
    new_list = List(title=list_data.title, board_id=list_data.board_id)
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list


@router.get("/", response_model=list[ListOut])
def get_lists(board_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_membership_or_404(db, board_id, current_user)  # any role may view
    return db.query(List).filter(List.board_id == board_id).all()


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    the_list, _ = get_board_via_list_or_404(db, list_id, current_user, allowed_roles=MANAGE_ROLES)
    db.delete(the_list)
    db.commit()
    return None
