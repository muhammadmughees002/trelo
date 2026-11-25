from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.board_member import BoardMember
from app.models.workspace_member import WorkspaceMember
from app.models.list import List
from app.models.card import Card
from app.models.user import User

MANAGE_ROLES = ("admin", "manager")


def get_workspace_membership_or_404(
    db: Session,
    workspace_id: int,
    current_user: User,
    allowed_roles: tuple[str, ...] | None = None,
) -> WorkspaceMember:
    """Same convention as get_membership_or_404, one level up: 404s
    (never 403) whether the workspace doesn't exist, the user isn't a
    member, or the member's role isn't in allowed_roles."""
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if allowed_roles is not None and membership.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return membership


def get_membership_or_404(
    db: Session,
    board_id: int,
    current_user: User,
    allowed_roles: tuple[str, ...] | None = None,
) -> BoardMember:
    """Fetch current_user's BoardMember row for this board.

    404s (never 403) in every failure case — board doesn't exist, user
    isn't a member at all, or user is a member but not one of
    allowed_roles — so a caller can never distinguish "no such board" from
    "that board isn't yours," matching this codebase's existing
    error-hiding convention everywhere else.
    """
    membership = (
        db.query(BoardMember)
        .filter(
            BoardMember.board_id == board_id,
            BoardMember.user_id == current_user.id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    if allowed_roles is not None and membership.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return membership


def get_board_via_list_or_404(
    db: Session,
    list_id: int,
    current_user: User,
    allowed_roles: tuple[str, ...] | None = None,
) -> tuple[List, BoardMember]:
    """Fetch a List, but only if current_user has (optionally role-gated)
    membership on its Board. Mirrors get_membership_or_404's 404-only,
    same-message convention for every failure case."""
    the_list = db.query(List).filter(List.id == list_id).first()
    if the_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    try:
        membership = get_membership_or_404(db, the_list.board_id, current_user, allowed_roles)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return the_list, membership


def get_card_via_list_or_404(
    db: Session,
    card_id: int,
    current_user: User,
    allowed_roles: tuple[str, ...] | None = None,
) -> tuple[Card, List, BoardMember]:
    """Fetch a Card, but only if current_user has (optionally role-gated)
    membership on the Board its List belongs to."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    try:
        the_list, membership = get_board_via_list_or_404(
            db, card.list_id, current_user, allowed_roles
        )
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card, the_list, membership


def can_edit_card(card: Card, membership: BoardMember, current_user: User) -> bool:
    """admin/manager can edit any card on the board; a developer can only
    edit a card assigned to themself."""
    if membership.role in MANAGE_ROLES:
        return True
    return card.assigned_user_id == current_user.id


def resolve_assignee_within_board(
    db: Session, board_id: int, assignee_email: str | None
) -> int | None:
    """Look up a user by email for card assignment, but only accept them
    if they are already a member of THIS specific board — the new
    constraint that stops a manager from assigning tickets to people
    outside their own board."""
    if assignee_email is None:
        return None
    user = db.query(User).filter(User.email == assignee_email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user with that email"
        )
    is_member = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
        .first()
        is not None
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That user is not a member of this board"
        )
    return user.id
