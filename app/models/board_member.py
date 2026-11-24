from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from app.db.base import Base


class BoardMember(Base):
    __tablename__ = "board_members"
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # "admin" | "manager" | "developer" — validated at the Pydantic layer,
    # not a DB-level enum, so adding/renaming roles later doesn't need a
    # schema migration.
    role = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_member"),
    )
