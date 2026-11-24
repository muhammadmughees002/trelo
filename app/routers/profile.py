from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.board_member import BoardMember
from app.models.user import User
from app.schemas.user import UserOut, UserProfileOut, UserProfileUpdate, DeveloperEmailUpdate

router = APIRouter(prefix="/users", tags=["profile"])


def _shared_board_memberships(db: Session, user_a_id: int, user_b_id: int):
    """All (membership_a, membership_b) pairs for boards both users are on."""
    rows_a = {m.board_id: m for m in db.query(BoardMember).filter(BoardMember.user_id == user_a_id)}
    rows_b = {m.board_id: m for m in db.query(BoardMember).filter(BoardMember.user_id == user_b_id)}
    shared_board_ids = rows_a.keys() & rows_b.keys()
    return [(rows_a[bid], rows_b[bid]) for bid in shared_board_ids]


def _can_view_profile(db: Session, viewer: User, target: User) -> bool:
    """Shared-board + role hierarchy visibility rule (confirmed with user):
    - Admin can view Manager/Developer profiles on a board they admin.
    - Manager can view Developer profiles on a board they manage.
    - Developer cannot view anyone else's profile.
    - Manager cannot view an Admin's profile.
    Two users with no board in common are invisible to each other — there
    is deliberately no global user directory/search.
    """
    if viewer.id == target.id:
        return True
    for viewer_m, target_m in _shared_board_memberships(db, viewer.id, target.id):
        if viewer_m.role == "admin" and target_m.role in ("manager", "developer"):
            return True
        if viewer_m.role == "manager" and target_m.role == "developer":
            return True
    return False


def _can_edit_developer_email(db: Session, requester: User, target: User) -> bool:
    """A Manager or Admin may change a Developer's email, but ONLY on a
    board they share with that developer in the right roles.

    ⚠️ Security note: letting someone else change a user's login email is
    unusual — email often doubles as the account-recovery/identity field.
    This is built exactly as the project owner specified, but if this ever
    goes beyond a learning project, consider logging these changes and/or
    notifying the affected developer when it happens.
    """
    for requester_m, target_m in _shared_board_memberships(db, requester.id, target.id):
        if requester_m.role in ("admin", "manager") and target_m.role == "developer":
            return True
    return False


@router.get("/{user_id}/profile", response_model=UserProfileOut)
def get_profile(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.id == user_id).first()
    # 404 for "no such user" and "exists but you can't see it" alike —
    # never confirm a user id exists to someone without visibility rights.
    if target is None or not _can_view_profile(db, current_user, target):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return target


@router.put("/me/profile", response_model=UserOut)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/{user_id}/email", response_model=UserOut)
def update_developer_email(
    user_id: int,
    email_data: DeveloperEmailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None or not _can_edit_developer_email(db, current_user, target):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    existing = db.query(User).filter(User.email == email_data.email, User.id != user_id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    target.email = email_data.email
    db.commit()
    db.refresh(target)
    return target
