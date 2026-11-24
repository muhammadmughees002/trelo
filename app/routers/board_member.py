from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import get_membership_or_404
from app.models.board_member import BoardMember
from app.models.user import User
from app.schemas.board_member import BoardMemberCreate, BoardMemberRoleUpdate, BoardMemberOut

router = APIRouter(prefix="/boards/{board_id}/members", tags=["board_members"])


@router.post("", response_model=BoardMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    board_id: int,
    member_data: BoardMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership_or_404(db, board_id, current_user, allowed_roles=("admin",))

    user = db.query(User).filter(User.email == member_data.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user with that email")

    existing = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member of this board")

    new_member = BoardMember(board_id=board_id, user_id=user.id, role=member_data.role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@router.get("", response_model=list[BoardMemberOut])
def list_members(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership_or_404(db, board_id, current_user)  # any role may view
    return db.query(BoardMember).filter(BoardMember.board_id == board_id).all()


@router.put("/{user_id}", response_model=BoardMemberOut)
def update_member_role(
    board_id: int,
    user_id: int,
    role_data: BoardMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership_or_404(db, board_id, current_user, allowed_roles=("admin",))

    member = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Guard against demoting the last remaining admin, which would
    # orphan the board (nobody left who can manage membership or delete it).
    if member.role == "admin" and role_data.role != "admin":
        other_admins = (
            db.query(BoardMember)
            .filter(
                BoardMember.board_id == board_id,
                BoardMember.role == "admin",
                BoardMember.user_id != user_id,
            )
            .count()
        )
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin on this board",
            )

    member.role = role_data.role
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    board_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership_or_404(db, board_id, current_user, allowed_roles=("admin",))

    member = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.role == "admin":
        other_admins = (
            db.query(BoardMember)
            .filter(
                BoardMember.board_id == board_id,
                BoardMember.role == "admin",
                BoardMember.user_id != user_id,
            )
            .count()
        )
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin on this board",
            )

    db.delete(member)
    db.commit()
    return None
