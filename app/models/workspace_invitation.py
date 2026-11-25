from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.db.base import Base


class WorkspaceInvitation(Base):
    __tablename__ = "workspace_invitations"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    invited_email = Column(String, nullable=False)
    # "admin" | "manager" — same restriction as workspace membership itself.
    role = Column(String, nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # "pending" | "accepted" | "declined"
    status = Column(String, nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)
