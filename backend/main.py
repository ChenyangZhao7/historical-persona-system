import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from env import load_env

load_env()

from database import init_db  # noqa: E402  (must run after load_env)
from services import llm  # noqa: E402
from routers.figures import router as figures_router  # noqa: E402
from routers.match import router as match_router  # noqa: E402
from routers.reverse import router as reverse_router  # noqa: E402
from routers.reconstruct import router as reconstruct_router  # noqa: E402
from routers.predict import router as predict_router  # noqa: E402
from routers.analyze import router as analyze_router  # noqa: E402
from routers.chat import router as chat_router  # noqa: E402
from routers.graph import router as graph_router  # noqa: E402
from routers.locations import router as locations_router  # noqa: E402
from routers.relics import router as relics_router  # noqa: E402

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

# Comma-separated list. Defaults cover the Vite dev server only; in production
# the API serves the built frontend from the same origin, so no CORS is needed.
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _allowed_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", DEFAULT_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not llm.available():
        raise RuntimeError(
            f"No API key configured for LLM_PROVIDER={llm.provider()}. "
            "Copy .env.example to .env and add the key, or export it before starting the server."
        )
    init_db()
    yield


app = FastAPI(title="Historical Persona System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    figures_router,
    match_router,
    reverse_router,
    reconstruct_router,
    predict_router,
    analyze_router,
    chat_router,
    graph_router,
    locations_router,
    relics_router,
):
    app.include_router(router)

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file = FRONTEND_DIST / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {"message": "Historical Persona System API is running"}
