from sqlalchemy import Column , Integer , String , DateTime ,func , ForeignKey
from app.db.base import Base

class Board(Base):
    __tablename__="boards"
    id=Column(Integer,primary_key=True)
    title = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )