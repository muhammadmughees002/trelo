from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.permissions import get_workspace_membership_or_404
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def post_workspace(workspace_data: WorkspaceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_workspace = Workspace(name=workspace_data.name, owner_id=current_user.id)
    db.add(new_workspace)
    db.flush()  # assigns new_workspace.id without ending the transaction

    # The creator is always auto-enrolled as this workspace's first Admin,
    # same pattern as board creation.
    db.add(WorkspaceMember(workspace_id=new_workspace.id, user_id=current_user.id, role="admin"))

    db.commit()
    db.refresh(new_workspace)
    return new_workspace


@router.get("", response_model=list[WorkspaceOut])
def get_workspaces(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == current_user.id)
        .all()
    )


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_workspace_membership_or_404(db, workspace_id, current_user)  # any role may view
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_workspace_membership_or_404(db, workspace_id, current_user, allowed_roles=("admin",))
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    db.delete(workspace)  # cascades to its boards -> lists -> cards, and its workspace_members
    db.commit()
    return None
