from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import get_membership_or_404, get_workspace_membership_or_404, MANAGE_ROLES
from app.models.board import Board
from app.models.board_member import BoardMember
from app.models.list import List
from app.models.user import User
from app.schemas.board import BoardCreate, BoardOut

router = APIRouter(prefix="/boards", tags=["boards"])

# Every new board starts with this Kanban-style workflow. These are just
# a convenient starting point, not a fixed structure — lists created this
# way can still be freely renamed, deleted, or added to afterward.
DEFAULT_LIST_TITLES = ["To Do", "In Progress", "Checking", "Done"]


@router.post("", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def post_board(board_data: BoardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only a workspace admin/manager may create a board inside it.
    get_workspace_membership_or_404(db, board_data.workspace_id, current_user, allowed_roles=MANAGE_ROLES)

    new_board = Board(title=board_data.title, owner_id=current_user.id, workspace_id=board_data.workspace_id)
    db.add(new_board)
    db.flush()  # assigns new_board.id without ending the transaction

    # The creator is always auto-enrolled as this board's first Admin —
    # from here on, authorization checks go through board_members, not
    # Board.owner_id directly (owner_id is kept only as a historical record
    # of who originally created the board).
    db.add(BoardMember(board_id=new_board.id, user_id=current_user.id, role="admin"))

    for title in DEFAULT_LIST_TITLES:
        db.add(List(title=title, board_id=new_board.id))

    db.commit()
    db.refresh(new_board)
    return new_board


@router.get("", response_model=list[BoardOut])
def get_boards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Board)
        .join(BoardMember, BoardMember.board_id == Board.id)
        .filter(BoardMember.user_id == current_user.id)
        .all()
    )


@router.get("/{board_id}", response_model=BoardOut)
def get_board(board_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_membership_or_404(db, board_id, current_user)  # any role may view
    board = db.query(Board).filter(Board.id == board_id).first()
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_membership_or_404(db, board_id, current_user, allowed_roles=("admin",))
    board = db.query(Board).filter(Board.id == board_id).first()
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    db.delete(board)
    db.commit()
    return None
