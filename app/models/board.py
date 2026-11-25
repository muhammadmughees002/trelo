from sqlalchemy import Column , Integer , String , DateTime ,func , ForeignKey
from app.db.base import Base

class Board(Base):
    __tablename__="boards"
    id=Column(Integer,primary_key=True)
    title = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Nullable for now so the migration can backfill existing boards
    # before a follow-up migration tightens this to NOT NULL.
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )