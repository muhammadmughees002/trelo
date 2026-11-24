"""cascade delete board_members, lists, cards when parent is deleted

Revision ID: f5b26371f654
Revises: be28bc475d92
Create Date: 2026-11-24 19:06:36.761519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5b26371f654'
down_revision: Union[str, Sequence[str], None] = 'be28bc475d92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make deleting a Board also remove its memberships/lists, and
    deleting a List also remove its cards.

    Without this, DELETE /boards/{id} would fail outright: Postgres
    rejects deleting a row that other rows still reference by foreign
    key. Only parent->child structural relationships cascade here —
    users.id is never cascaded (deleting a user should not silently
    delete boards/cards elsewhere; that's a separate decision for later).
    """
    op.drop_constraint('board_members_board_id_fkey', 'board_members', type_='foreignkey')
    op.create_foreign_key(
        'board_members_board_id_fkey', 'board_members', 'boards',
        ['board_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('lists_board_id_fkey', 'lists', type_='foreignkey')
    op.create_foreign_key(
        'lists_board_id_fkey', 'lists', 'boards',
        ['board_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('cards_list_id_fkey', 'cards', type_='foreignkey')
    op.create_foreign_key(
        'cards_list_id_fkey', 'cards', 'lists',
        ['list_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Restore the original (non-cascading) foreign keys."""
    op.drop_constraint('cards_list_id_fkey', 'cards', type_='foreignkey')
    op.create_foreign_key(
        'cards_list_id_fkey', 'cards', 'lists', ['list_id'], ['id']
    )

    op.drop_constraint('lists_board_id_fkey', 'lists', type_='foreignkey')
    op.create_foreign_key(
        'lists_board_id_fkey', 'lists', 'boards', ['board_id'], ['id']
    )

    op.drop_constraint('board_members_board_id_fkey', 'board_members', type_='foreignkey')
    op.create_foreign_key(
        'board_members_board_id_fkey', 'board_members', 'boards', ['board_id'], ['id']
    )
