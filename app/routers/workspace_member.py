from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import get_workspace_membership_or_404
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.schemas.workspace_member import WorkspaceMemberRoleUpdate, WorkspaceMemberOut

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["workspace_members"])

# Adding a member directly has been replaced by the invite+accept flow —
# see routers/invitation.py's POST /workspaces/{workspace_id}/invitations.
# Membership rows are now only ever created by accepting an invitation.


@router.get("", response_model=list[WorkspaceMemberOut])
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_membership_or_404(db, workspace_id, current_user)  # any role may view
    return db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()


def _count_other_admins(db: Session, workspace_id: int, excluding_user_id: int) -> int:
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == "admin",
            WorkspaceMember.user_id != excluding_user_id,
        )
        .count()
    )


@router.put("/{user_id}", response_model=WorkspaceMemberOut)
def update_member_role(
    workspace_id: int,
    user_id: int,
    role_data: WorkspaceMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_membership_or_404(db, workspace_id, current_user, allowed_roles=("admin",))

    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Guard against demoting the last remaining admin, same reasoning as
    # the board-level version: don't let a workspace end up with nobody
    # who can manage it.
    if member.role == "admin" and role_data.role != "admin":
        if _count_other_admins(db, workspace_id, user_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin on this workspace",
            )

    member.role = role_data.role
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_membership_or_404(db, workspace_id, current_user, allowed_roles=("admin",))

    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.role == "admin" and _count_other_admins(db, workspace_id, user_id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last admin on this workspace",
        )

    db.delete(member)
    db.commit()
    return None
