"""The application object. `run.py` serves it — with what the platform adds to every app: its
styles and scripts at /static/platform/, large uploads at /media, and score.yaml's access with the
security headers on every request (ajnkit.web.platform). Not added here.

Wiring only — pages in views.py, JSON in api.py, background work in tasks.py,
schema in models.py. Do not add request handling here.

Keep `src/__init__.py` empty: anything in it runs on every `import src.*`.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api import router as api_router
from src.schemas.errors import register_exception_handlers
from src.spa import router as spa_router
from src.tasks import start_background_scheduler, stop_background_scheduler
from src.views import router as views_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    start_background_scheduler()
    try:
        yield
    finally:
        stop_background_scheduler()


# Swagger /api/docs — drawn by ajnkit.docs from the app's own files; ReDoc /api/redoc sends
# the reader there · schema /api/openapi.json — keep these paths: the platform
# opens exactly them without the sign-in when score.yaml's route says `docs: public`. Under
# `auth: none` they are open to the network anyway. Set them to None to hide the surface.
app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

register_exception_handlers(app)

# Paths resolve from this file, never the working directory.
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

app.include_router(views_router)
app.include_router(api_router, prefix="/api")
app.include_router(api_router)
app.include_router(spa_router)
