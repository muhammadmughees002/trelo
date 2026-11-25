from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.user import router as user_router
from app.routers.board import router as board_router
from app.routers.list import router as list_router
from app.routers.card import router as card_router
from app.routers.board_member import router as board_member_router
from app.routers.profile import router as profile_router
from app.routers.workspace import router as workspace_router
from app.routers.workspace_member import router as workspace_member_router

app = FastAPI()

# Kept permissive for local development. Tighten allow_origins before
# deploying anywhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(board_router)
app.include_router(list_router)
app.include_router(card_router)
app.include_router(board_member_router)
app.include_router(profile_router)
app.include_router(workspace_router)
app.include_router(workspace_member_router)

# Serves everything in static/ (including index.html) from the same
# origin as the API, at http://127.0.0.1:8000/static/...
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
