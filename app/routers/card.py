from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import (
    get_board_via_list_or_404,
    get_card_via_list_or_404,
    can_edit_card,
    resolve_assignee_within_board,
    MANAGE_ROLES,
)
from app.models.card import Card
from app.models.user import User
from app.schemas.card import CardCreate, CardUpdate, CardOut

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("/", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    card_data: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admin/manager may create cards.
    the_list, _ = get_board_via_list_or_404(db, card_data.list_id, current_user, allowed_roles=MANAGE_ROLES)
    assigned_user_id = resolve_assignee_within_board(db, the_list.board_id, card_data.assignee_email)

    new_card = Card(
        title=card_data.title,
        description=card_data.description,
        list_id=card_data.list_id,
        assigned_user_id=assigned_user_id,
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card


@router.get("/", response_model=list[CardOut])
def get_cards(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    get_board_via_list_or_404(db, list_id, current_user)  # any role may view
    return db.query(Card).filter(Card.list_id == list_id).all()


@router.put("/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    card_data: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Any member can reach this far (no role filter yet) — the real check
    # is can_edit_card below: admin/manager edit anything, a developer may
    # only edit a card currently assigned to themself.
    card, the_list, membership = get_card_via_list_or_404(db, card_id, current_user)
    if not can_edit_card(card, membership, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

    if card_data.title is not None:
        card.title = card_data.title
    if card_data.description is not None:
        card.description = card_data.description

    if card_data.unassign:
        if membership.role not in MANAGE_ROLES:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        card.assigned_user_id = None
    elif card_data.assignee_email is not None:
        if membership.role not in MANAGE_ROLES:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        card.assigned_user_id = resolve_assignee_within_board(
            db, the_list.board_id, card_data.assignee_email
        )

    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Deleting (unlike editing your own assigned card) always requires
    # admin/manager — a developer never deletes, even their own card.
    card, _, _ = get_card_via_list_or_404(db, card_id, current_user, allowed_roles=MANAGE_ROLES)
    db.delete(card)
    db.commit()
    return None
