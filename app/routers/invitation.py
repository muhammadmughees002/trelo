from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.dependencies import get_db, get_current_user
from app.core.permissions import (
    get_membership_or_404,
    get_workspace_membership_or_404,
    assert_can_invite,
    BOARD_INVITABLE_ROLES,
    WORKSPACE_INVITABLE_ROLES,
    MANAGE_ROLES,
)
from app.models.user import User
from app.models.board import Board
from app.models.board_member import BoardMember
from app.models.board_invitation import BoardInvitation
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.workspace_invitation import WorkspaceInvitation
from app.schemas.invitation import (
    WorkspaceInvitationCreate,
    BoardInvitationCreate,
    WorkspaceInvitationOut,
    BoardInvitationOut,
    MyInvitationOut,
)

router = APIRouter(tags=["invitations"])


# ---------------- Create (send) an invitation ----------------

@router.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=WorkspaceInvitationOut,
    status_code=status.HTTP_201_CREATED,
)
def invite_to_workspace(
    workspace_id: int,
    invite_data: WorkspaceInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = get_workspace_membership_or_404(db, workspace_id, current_user, allowed_roles=MANAGE_ROLES)
    assert_can_invite(membership.role, invite_data.role, WORKSPACE_INVITABLE_ROLES)

    target_user = db.query(User).filter(User.email == invite_data.email).first()
    if target_user is not None:
        already_member = (
            db.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user.id)
            .first()
        )
        if already_member is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member of this workspace")

    existing_pending = (
        db.query(WorkspaceInvitation)
        .filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.invited_email == invite_data.email,
            WorkspaceInvitation.status == "pending",
        )
        .first()
    )
    if existing_pending is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An invitation is already pending for this email")

    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        invited_email=invite_data.email,
        role=invite_data.role,
        invited_by_id=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@router.post(
    "/boards/{board_id}/invitations",
    response_model=BoardInvitationOut,
    status_code=status.HTTP_201_CREATED,
)
def invite_to_board(
    board_id: int,
    invite_data: BoardInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = get_membership_or_404(db, board_id, current_user, allowed_roles=MANAGE_ROLES)
    assert_can_invite(membership.role, invite_data.role, BOARD_INVITABLE_ROLES)

    target_user = db.query(User).filter(User.email == invite_data.email).first()
    if target_user is not None:
        already_member = (
            db.query(BoardMember)
            .filter(BoardMember.board_id == board_id, BoardMember.user_id == target_user.id)
            .first()
        )
        if already_member is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member of this board")

    existing_pending = (
        db.query(BoardInvitation)
        .filter(
            BoardInvitation.board_id == board_id,
            BoardInvitation.invited_email == invite_data.email,
            BoardInvitation.status == "pending",
        )
        .first()
    )
    if existing_pending is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An invitation is already pending for this email")

    invitation = BoardInvitation(
        board_id=board_id,
        invited_email=invite_data.email,
        role=invite_data.role,
        invited_by_id=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


# ---------------- View pending invitations (sender's side) ----------------

@router.get("/workspaces/{workspace_id}/invitations", response_model=list[WorkspaceInvitationOut])
def list_workspace_invitations(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_membership_or_404(db, workspace_id, current_user, allowed_roles=MANAGE_ROLES)
    return (
        db.query(WorkspaceInvitation)
        .filter(WorkspaceInvitation.workspace_id == workspace_id, WorkspaceInvitation.status == "pending")
        .all()
    )


@router.get("/boards/{board_id}/invitations", response_model=list[BoardInvitationOut])
def list_board_invitations(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership_or_404(db, board_id, current_user, allowed_roles=MANAGE_ROLES)
    return (
        db.query(BoardInvitation)
        .filter(BoardInvitation.board_id == board_id, BoardInvitation.status == "pending")
        .all()
    )


# ---------------- My pending invitations (recipient's side) ----------------

@router.get("/invitations/me", response_model=list[MyInvitationOut])
def my_invitations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results: list[MyInvitationOut] = []

    ws_invites = (
        db.query(WorkspaceInvitation)
        .filter(WorkspaceInvitation.invited_email == current_user.email, WorkspaceInvitation.status == "pending")
        .all()
    )
    for inv in ws_invites:
        workspace = db.query(Workspace).filter(Workspace.id == inv.workspace_id).first()
        results.append(MyInvitationOut(
            id=inv.id, kind="workspace", target_id=inv.workspace_id,
            target_name=workspace.name if workspace else "(deleted workspace)",
            role=inv.role, created_at=inv.created_at,
        ))

    board_invites = (
        db.query(BoardInvitation)
        .filter(BoardInvitation.invited_email == current_user.email, BoardInvitation.status == "pending")
        .all()
    )
    for inv in board_invites:
        board = db.query(Board).filter(Board.id == inv.board_id).first()
        results.append(MyInvitationOut(
            id=inv.id, kind="board", target_id=inv.board_id,
            target_name=board.title if board else "(deleted board)",
            role=inv.role, created_at=inv.created_at,
        ))

    return results


# ---------------- Accept / decline ----------------

def _get_own_pending_workspace_invitation(db: Session, invitation_id: int, current_user: User) -> WorkspaceInvitation:
    invitation = (
        db.query(WorkspaceInvitation)
        .filter(WorkspaceInvitation.id == invitation_id, WorkspaceInvitation.invited_email == current_user.email)
        .first()
    )
    # 404 whether it doesn't exist, isn't yours, or was already resolved —
    # same error-hiding convention used everywhere else in this project.
    if invitation is None or invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    return invitation


def _get_own_pending_board_invitation(db: Session, invitation_id: int, current_user: User) -> BoardInvitation:
    invitation = (
        db.query(BoardInvitation)
        .filter(BoardInvitation.id == invitation_id, BoardInvitation.invited_email == current_user.email)
        .first()
    )
    if invitation is None or invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    return invitation


@router.post("/invitations/workspace/{invitation_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_workspace_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = _get_own_pending_workspace_invitation(db, invitation_id, current_user)

    already_member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == invitation.workspace_id, WorkspaceMember.user_id == current_user.id)
        .first()
    )
    if already_member is None:
        db.add(WorkspaceMember(workspace_id=invitation.workspace_id, user_id=current_user.id, role=invitation.role))

    invitation.status = "accepted"
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/invitations/workspace/{invitation_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_workspace_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = _get_own_pending_workspace_invitation(db, invitation_id, current_user)
    invitation.status = "declined"
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/invitations/board/{invitation_id}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_board_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = _get_own_pending_board_invitation(db, invitation_id, current_user)

    already_member = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == invitation.board_id, BoardMember.user_id == current_user.id)
        .first()
    )
    if already_member is None:
        db.add(BoardMember(board_id=invitation.board_id, user_id=current_user.id, role=invitation.role))

    invitation.status = "accepted"
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/invitations/board/{invitation_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_board_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = _get_own_pending_board_invitation(db, invitation_id, current_user)
    invitation.status = "declined"
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    return None
