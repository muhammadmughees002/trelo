"""backfill board_members admin rows for existing owners

Revision ID: be28bc475d92
Revises: 29e8dfcc9176
Create Date: 2026-11-24 19:05:24.080855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be28bc475d92'
down_revision: Union[str, Sequence[str], None] = '29e8dfcc9176'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Give every existing board's owner an 'admin' BoardMember row.

    Required because the new authorization model checks board_members
    instead of boards.owner_id — without this, every board created before
    this migration would have zero members, locking its own owner out.
    """
    op.execute(
        """
        INSERT INTO board_members (board_id, user_id, role, created_at)
        SELECT b.id, b.owner_id, 'admin', now()
        FROM boards b
        WHERE NOT EXISTS (
            SELECT 1 FROM board_members bm
            WHERE bm.board_id = b.id AND bm.user_id = b.owner_id
        )
        """
    )


def downgrade() -> None:
    """Remove only the rows this migration would have created.

    Narrowly scoped to admin rows that exactly match a board's owner_id,
    so it doesn't delete memberships added by hand after this migration
    ran (e.g. a manager/developer added later, or a re-added admin row).
    """
    op.execute(
        """
        DELETE FROM board_members bm
        USING boards b
        WHERE bm.board_id = b.id
          AND bm.user_id = b.owner_id
          AND bm.role = 'admin'
        """
    )
