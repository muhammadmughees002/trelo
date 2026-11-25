from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.user import router as user_router

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

# Serves everything in static/ (including index.html) from the same
# origin as the API, at http://127.0.0.1:8000/static/...
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
