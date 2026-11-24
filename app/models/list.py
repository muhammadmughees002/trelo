from app.db.base import Base
from sqlalchemy import Column , Integer , String , DateTime ,func , ForeignKey

class List(Base):
    __tablename__="lists"
    id=Column(Integer,primary_key=True)
    title=Column(String,nullable=False)
    board_id = Column(Integer,ForeignKey("boards.id", ondelete="CASCADE"),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)